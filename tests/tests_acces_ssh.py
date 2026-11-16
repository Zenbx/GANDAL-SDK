#!/usr/bin/env python3
"""Verifications de l acces SSH depuis le SDK, avec un VRAI signeur.

    python3 tests_acces_ssh.py

Le signeur est lance pour de bon, avec une autorite de test, et IAM est
remplace par un faux qui dit « permit » ou « deny » sur commande. Ce qui est
eprouve n est donc pas une simulation du protocole mais le protocole.
"""
from __future__ import annotations

import http.server
import importlib.util
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time

ICI = os.path.dirname(os.path.abspath(__file__))
OK = 0
ECHECS: list[str] = []


def verifier(libelle: str, condition: bool, detail: str = "") -> None:
    global OK
    if condition:
        print(f"  OK      {libelle}")
        OK += 1
    else:
        print(f"  ECHEC   {libelle}" + (f"\n          {detail}" if detail else ""))
        ECHECS.append(libelle)


def charger(nom: str, chemin: str):
    spec = importlib.util.spec_from_file_location(nom, chemin)
    m = importlib.util.module_from_spec(spec)
    sys.modules[nom] = m
    spec.loader.exec_module(m)
    return m


T = tempfile.mkdtemp(prefix="sdk-ssh-")
CA = os.path.join(T, "ca")
os.makedirs(CA, mode=0o700)
subprocess.run(["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-f",
                os.path.join(CA, "autorite")], check=True)
os.chmod(os.path.join(CA, "autorite"), 0o600)
with open(os.path.join(CA, "serie"), "w") as f:
    f.write("0")
os.chmod(os.path.join(CA, "serie"), 0o600)

# ── un faux IAM, qui dit ce qu on lui demande de dire ────────────────────────
VERDICT = {"decision": "permit", "motif": "proprietaire",
           "explication": "vous etes proprietaire", "correlation_id": "01TEST"}
VUS: list[dict] = []


class FauxIam(http.server.BaseHTTPRequestHandler):
    def do_POST(self):                                       # noqa: N802
        taille = int(self.headers.get("Content-Length") or 0)
        VUS.append({
            "chemin": self.path,
            "autorisation": self.headers.get("Authorization", ""),
            "corps": json.loads(self.rfile.read(taille) or b"{}"),
        })
        donnees = json.dumps(VERDICT).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(donnees)))
        self.end_headers()
        self.wfile.write(donnees)

    def log_message(self, *a):                               # noqa: A002
        pass


def port_libre() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


P_IAM = port_libre()
srv_iam = http.server.ThreadingHTTPServer(("127.0.0.1", P_IAM), FauxIam)
threading.Thread(target=srv_iam.serve_forever, daemon=True).start()

# ── le VRAI signeur, en clair sur la boucle locale pour ce test ──────────────
os.environ["GANDAL_SSH_CA"] = CA
os.environ["GANDAL_SSH_IAM"] = f"http://127.0.0.1:{P_IAM}/v1"
# LE SIGNEUR VIT DANS LE DEPOT GANDAL, PAS ICI. Ce test traverse donc deux
# depots, et il doit se SAUTER proprement quand le second n est pas la —
# casser la suite du SDK parce qu un autre depot manque ferait supprimer le
# test, pas installer le depot.
_PISTES = [
    os.environ.get("GANDAL_SIGNEUR_SRC", ""),
    os.path.join(os.path.dirname(os.path.dirname(ICI)), "iam", "ssh-ca", "signeur.py"),
    os.path.expanduser("~/Projets/Gandal/iam/ssh-ca/signeur.py"),
]
_signeur = next((c for c in _PISTES if c and os.path.exists(c)), "")
if not _signeur:
    print("SAUTE — « signeur.py » du depot GANDAL introuvable.")
    print("  Poser GANDAL_SIGNEUR_SRC=<chemin de iam/ssh-ca/signeur.py>")
    print("  La preuve complete tourne dans le depot GANDAL.")
    sys.exit(0)

S = charger("signeur_test", _signeur)
S.CA = CA
S.IAM = f"http://127.0.0.1:{P_IAM}/v1"

P_SIG = port_libre()
srv_sig = http.server.ThreadingHTTPServer(("127.0.0.1", P_SIG), S.Gestionnaire)
threading.Thread(target=srv_sig.serve_forever, daemon=True).start()
time.sleep(0.2)

# Le module eprouve est celui de CE depot.
A = charger("acces_ssh_test",
            os.path.join(os.path.dirname(ICI), "src", "gandal_sdk",
                         "acces_ssh.py"))

try:
    print("le gestionnaire de contexte est obligatoire")
    a = A.AccesSsh("jeton-x", signeur=f"http://127.0.0.1:{P_SIG}")
    try:
        a.certificat("vm-1")
        verifier("hors « with », refus", False)
    except A.AccesRefuse as e:
        verifier("hors « with », refus", "with" in str(e), str(e))

    print("\nun jeton vide est refuse tout de suite")
    try:
        A.AccesSsh("")
        verifier("jeton vide -> refus", False)
    except A.AccesRefuse as e:
        verifier("jeton vide -> refus", "jeton" in str(e).lower(), str(e))

    print("\nle chemin heureux")
    with A.AccesSsh("jeton-de-pierre",
                    signeur=f"http://127.0.0.1:{P_SIG}",
                    sujet="etu-1", login="gandaladm") as acces:
        c = acces.certificat("poste-vision-01")
        verifier("un certificat est rendu", c.serie >= 1, str(c.serie))
        verifier("le fichier de certificat existe",
                 os.path.exists(c.certificat))
        verifier("il est en 600",
                 oct(os.stat(c.certificat).st_mode)[-3:] == "600")
        verifier("la cle privee ephemere existe", os.path.exists(c.cle_privee))
        verifier("le suivi IAM est relaye", c.correlation_id == "01TEST",
                 c.correlation_id)

        print("\nce que le signeur a VRAIMENT demande a IAM")
        d = VUS[-1]
        verifier("l action demandee est « vm:ssh »",
                 d["corps"].get("action") == "vm:ssh", str(d["corps"]))
        verifier("la ressource est LA VM demandee",
                 d["corps"].get("ressource", {}).get("id") == "poste-vision-01",
                 str(d["corps"].get("ressource")))
        verifier("le JETON DE L UTILISATEUR est relaye, pas celui du signeur",
                 d["autorisation"] == "Bearer jeton-de-pierre",
                 d["autorisation"])

        print("\nle certificat ne vaut que pour CE compte et CETTE VM")
        detail = subprocess.run(["ssh-keygen", "-L", "-f", c.certificat],
                                capture_output=True, text=True).stdout
        verifier("l identite nomme le sujet et la VM",
                 "etu-1@poste-vision-01" in detail, detail[:200])
        verifier("le seul compte autorise est gandaladm",
                 "gandaladm" in detail, detail[:300])
        verifier("permit-pty accorde, transfert de ports REFUSE",
                 "permit-pty" in detail
                 and "permit-port-forwarding" not in detail, detail[-300:])

        print("\nla ligne ssh")
        argv = acces.commande_ssh("poste-vision-01", c)
        verifier("« IdentitiesOnly=yes » est pose",
                 "IdentitiesOnly=yes" in argv, str(argv))
        verifier("le certificat est passe par « CertificateFile »",
                 any(x.startswith("CertificateFile=") for x in argv), str(argv))
        verifier("le compte est dans la cible",
                 argv[-1] == "gandaladm@poste-vision-01", argv[-1])

        garde_cle, garde_cert = c.cle_privee, c.certificat

        print("\nIAM refuse : le SDK relaie le motif")
        VERDICT.update({"decision": "deny", "motif": "quota_depasse",
                        "explication": "il vous reste 0 vCPU sur 4"})
        try:
            acces.certificat("poste-vision-02")
            verifier("un refus d IAM leve AccesRefuse", False)
        except A.AccesRefuse as e:
            verifier("un refus d IAM leve AccesRefuse", True)
            verifier("et le MOTIF d IAM est dans le message",
                     "quota_depasse" in str(e) or "0 vCPU" in str(e), str(e))
        VERDICT.update({"decision": "permit", "motif": "proprietaire"})

    print("\nle menage")
    verifier("la cle ephemere est DETRUITE en sortant du « with »",
             not os.path.exists(garde_cle), garde_cle)
    verifier("le certificat aussi", not os.path.exists(garde_cert))

    print("\nmenage meme sur exception")
    chemins = {}
    try:
        with A.AccesSsh("j", signeur=f"http://127.0.0.1:{P_SIG}",
                        sujet="etu-1") as acces2:
            c2 = acces2.certificat("vm-essai")
            chemins["cle"] = c2.cle_privee
            raise RuntimeError("panne simulee")
    except RuntimeError:
        pass
    verifier("la cle est detruite malgre l exception",
             not os.path.exists(chemins["cle"]), chemins["cle"])

    print("\nsigneur injoignable")
    with A.AccesSsh("j", signeur="http://127.0.0.1:1", sujet="e") as acces3:
        try:
            acces3.certificat("vm-1")
            verifier("signeur muet -> SigneurIndisponible", False)
        except A.SigneurIndisponible:
            verifier("signeur muet -> SigneurIndisponible", True)
        except A.AccesRefuse:
            verifier("signeur muet -> SigneurIndisponible", False,
                     "AccesRefuse leve au lieu de SigneurIndisponible")
    verifier("« except AccesRefuse » attrape aussi la panne",
             issubclass(A.SigneurIndisponible, A.AccesRefuse))
finally:
    srv_sig.shutdown()
    srv_iam.shutdown()
    shutil.rmtree(T, ignore_errors=True)

print(f"\n=== {OK} verifications passees, {len(ECHECS)} en echec ===")
sys.exit(1 if ECHECS else 0)
