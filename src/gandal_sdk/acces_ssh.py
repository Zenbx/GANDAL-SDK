"""Accès SSH à une VM : demander le droit à IAM, puis entrer.

C EST ICI QUE CA DOIT VIVRE, et pas dans un script a part : c est avec le SDK
qu on travaille. Demander une VM, demander le droit d y entrer et y entrer sont
trois gestes du meme travail, et ils appartiennent au meme outil.

    from gandal_sdk.acces_ssh import AccesSsh

    with AccesSsh(jeton, signeur="https://10.30.0.30:8443") as a:
        a.entrer("poste-vision-01")                 # ouvre une session
        # ou, pour piloter soi-meme :
        cert = a.certificat("poste-vision-01")      # chemins + duree

CE QUE CE MODULE NE GARDE PAS. La paire de cles est EPHEMERE : creee pour la
session, dans un repertoire temporaire en 700, detruite en sortant du
gestionnaire de contexte. Rien ne s accumule dans ~/.ssh, donc rien n y survit
a un droit retire.

POURQUOI PAS LA CLE HABITUELLE DE L UTILISATEUR. Si on signait sa cle de
toujours, le certificat expirerait mais la cle resterait — et le jour ou elle
traine dans un depot ou sur un poste partage, elle vaut autant qu avant. Une
cle qui ne vit qu une session n a rien a fuir.

CE MODULE N EST PAS LE CONTROLE D ACCES, comme « garde.py » ne l est pas. Le
refus qui fait autorite vient du signeur, qui demande a IAM. Ici on ne fait que
poser la question et presenter la reponse. La difference avec « garde.py » est
qu ici le contournement ne sert a rien : sauter le SDK ne donne pas de
certificat, et sans certificat la VM ne repond pas.
"""
from __future__ import annotations

import getpass
import json
import os
import shutil
import ssl
import subprocess
import tempfile
import urllib.error
import urllib.request
from dataclasses import dataclass

CHEMIN = "/v1/ssh-certificat"


class AccesRefuse(Exception):
    """IAM a refusé, ou la demande est malformée. Le motif est dans le message."""


class SigneurIndisponible(AccesRefuse):
    """Le signeur ne répond pas.

    HERITE DE « AccesRefuse » A DESSEIN : un appelant qui écrit
    « except AccesRefuse » attrape les deux, et c est ce qu il veut presque
    toujours — dans les deux cas, on n entre pas. Qui doit distinguer une panne
    d un refus l attrape explicitement.
    """


@dataclass
class Certificat:
    """Ce qu'on a obtenu, et où c'est posé."""
    cle_privee: str
    certificat: str
    serie: int
    validite: str
    expire_vers: str
    correlation_id: str


class AccesSsh:
    """Demande des certificats SSH de courte durée, et ouvre des sessions."""

    def __init__(self, jeton: str, *, signeur: str = "",
                 autorite: str = "", sujet: str = "",
                 login: str = "gandaladm", delai_s: float = 15.0) -> None:
        if not jeton:
            # LE JETON EST CE QUI DIT A IAM **QUI** DEMANDE. Sans lui, le
            # signeur ne peut pas poser la question, et signer « au nom de
            # personne » serait une porte ouverte.
            raise AccesRefuse(
                "aucun jeton : s authentifier au portail d abord. C est ce "
                "jeton qui dit a IAM qui demande l acces.")
        self.jeton = jeton
        self.signeur = (signeur or os.environ.get(
            "GANDAL_SIGNEUR", "https://10.30.0.30:8443")).rstrip("/")
        self.autorite = autorite or os.environ.get("GANDAL_CA", "")
        self.sujet = sujet
        self.login = login
        self.delai_s = delai_s
        self._travail: str | None = None

    # ─── le gestionnaire de contexte : c est lui qui garantit le menage ────

    def __enter__(self) -> AccesSsh:
        self._travail = tempfile.mkdtemp(prefix="gandal-ssh-")
        os.chmod(self._travail, 0o700)
        return self

    def __exit__(self, *_) -> None:
        if self._travail:
            # LE MENAGE SE FAIT MEME SUR EXCEPTION. Une cle privee laissee dans
            # /tmp parce qu une erreur est remontee serait exactement le
            # probleme qu on cherche a eviter.
            shutil.rmtree(self._travail, ignore_errors=True)
            self._travail = None

    def _repertoire(self) -> str:
        if not self._travail:
            raise AccesRefuse(
                "AccesSsh s utilise dans un « with » : c est le seul moyen de "
                "garantir que la cle ephemere est detruite.")
        return self._travail

    # ─── obtenir un certificat ─────────────────────────────────────────────

    def certificat(self, vm: str, *, login: str = "",
                   sujet: str = "") -> Certificat:
        """Demande un certificat pour `vm`. Lève `AccesRefuse` si c'est non."""
        travail = self._repertoire()
        cle = os.path.join(travail, f"ephemere-{vm}")
        if not os.path.exists(cle):
            r = subprocess.run(
                ["ssh-keygen", "-q", "-t", "ed25519", "-N", "",
                 "-C", f"gandal-sdk {sujet or self.sujet or '?'}@{vm}",
                 "-f", cle],
                capture_output=True)
            if r.returncode != 0:
                raise AccesRefuse(
                    f"ssh-keygen echoue : "
                    f"{r.stderr.decode(errors='replace').strip()}")
        with open(cle + ".pub") as f:
            publique = f.read().strip()

        corps = json.dumps({
            "sujet": sujet or self.sujet,
            "vm": vm,
            "login": login or self.login,
            "cle_publique": publique,
        }).encode()
        requete = urllib.request.Request(
            self.signeur + CHEMIN, data=corps, method="POST",
            headers={"Content-Type": "application/json",
                     "Authorization": f"Bearer {self.jeton}"})
        contexte = ssl.create_default_context(
            cafile=os.path.expanduser(self.autorite) if self.autorite else None)
        try:
            with urllib.request.urlopen(requete, timeout=self.delai_s,
                                        context=contexte) as rep:
                reponse = json.loads(rep.read())
        except urllib.error.HTTPError as e:
            detail = e.read().decode(errors="replace")
            try:
                detail = json.loads(detail).get("erreur", detail)
            except ValueError:
                pass
            # LE MOTIF D IAM EST RELAYE TEL QUEL : il nomme la regle, et c est
            # ce qui permet a l utilisateur de comprendre sans ouvrir un ticket.
            raise AccesRefuse(f"{e.code} — {detail}") from e
        except OSError as e:
            raise SigneurIndisponible(
                f"signeur injoignable ({self.signeur}) : {e}") from e

        chemin_cert = cle + "-cert.pub"
        with open(chemin_cert, "w") as f:
            f.write(reponse["certificat"].strip() + "\n")
        os.chmod(chemin_cert, 0o600)
        return Certificat(
            cle_privee=cle, certificat=chemin_cert,
            serie=int(reponse.get("serie", 0)),
            validite=str(reponse.get("validite", "?")),
            expire_vers=str(reponse.get("expire_vers", "?")),
            correlation_id=str(reponse.get("correlation_id", "")))

    # ─── entrer ────────────────────────────────────────────────────────────

    def commande_ssh(self, vm: str, c: Certificat, *, hote: str = "",
                     login: str = "") -> list[str]:
        """La ligne `ssh` à lancer. Séparée pour pouvoir la montrer et la tester."""
        return [
            "ssh", "-i", c.cle_privee,
            # SANS « IdentitiesOnly », ssh essaie d abord toutes les cles de
            # l agent ; un refus de l une peut faire fermer la connexion avant
            # que le certificat ne soit presente.
            "-o", "IdentitiesOnly=yes",
            "-o", f"CertificateFile={c.certificat}",
            f"{login or self.login}@{hote or vm}",
        ]

    def entrer(self, vm: str, *, hote: str = "", login: str = "",
               commande: list[str] | None = None) -> int:
        """Obtient un certificat et ouvre la session. Rend le code de sortie."""
        c = self.certificat(vm, login=login)
        argv = self.commande_ssh(vm, c, hote=hote, login=login)
        return subprocess.run(argv + (commande or [])).returncode


# ─── la ligne de commande ──────────────────────────────────────────────────

def cli(argv: list[str] | None = None) -> int:
    """« gandal-ssh <vm> ». Point d entrée de la commande installée.

    ELLE N IMPORTE RIEN DU RESTE DU SDK, et c est voulu : entrer dans une VM
    doit marcher sur un poste qui n a ni httpx ni pydantic — par exemple une VM
    de la plateforme, qui n a pas d acces Internet pour les installer. Ce module
    n utilise que la bibliothèque standard.
    """
    import argparse
    import sys

    p = argparse.ArgumentParser(
        prog="gandal-ssh",
        description="Demande un certificat a IAM, puis entre dans la VM.")
    p.add_argument("vm", help="identifiant de la VM, tel qu IAM le connait")
    p.add_argument("--login", default="gandaladm",
                   help="le compte dans la VM (defaut : gandaladm)")
    p.add_argument("--sujet", default="",
                   help="le sujet IAM (defaut : le nom d utilisateur local)")
    p.add_argument("--signeur", default="",
                   help="adresse du signeur (defaut : GANDAL_SIGNEUR)")
    p.add_argument("--hote", default="",
                   help="adresse SSH de la VM si elle differe de son identifiant")
    p.add_argument("--autorite", default="",
                   help="l autorite TLS du signeur (defaut : GANDAL_CA)")
    p.add_argument("commande", nargs="*",
                   help="commande a lancer dans la VM, au lieu d un shell")
    a = p.parse_args(argv)

    jeton = os.environ.get("GANDAL_JETON", "")
    sujet = a.sujet or getpass.getuser()
    try:
        with AccesSsh(jeton, signeur=a.signeur, autorite=a.autorite,
                      sujet=sujet, login=a.login) as acces:
            c = acces.certificat(a.vm)
            print(f"certificat serie {c.serie}, valide {c.validite} "
                  f"(jusque vers {c.expire_vers})", file=sys.stderr)
            print(f"suivi IAM : {c.correlation_id or '-'}", file=sys.stderr)
            argv_ssh = acces.commande_ssh(a.vm, c, hote=a.hote)
            import subprocess as sp
            return sp.run(argv_ssh + list(a.commande)).returncode
    except AccesRefuse as e:
        # LE MOTIF D IAM EST RENDU TEL QUEL : il nomme la regle, et c est ce qui
        # permet a l utilisateur de comprendre sans ouvrir un ticket.
        print(f"ARRET — {e}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    import sys
    sys.exit(cli())
