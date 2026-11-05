"""Garde IAM côté CLIENT — la séquence du contrat, depuis le SDK.

CE QUE CE MODULE N EST PAS. Ce n est **pas** le contrôle d accès. Un garde-fou
dans un client est contournable : il suffit d appeler le backend directement, et
rien n est demandé à IAM. Le contrôle qui fait autorité vit dans le backend
(`iam/garde-serveur/` du dépôt GANDAL). Prendre celui-ci pour celui-là est la
façon la plus simple de croire qu on applique des quotas alors qu on les affiche.

CE QU IL APPORTE QUAND MEME, et ce n est pas rien :

  1. LA COMPTABILITE DEVIENT VRAIE. La réservation et la confirmation se font
     DANS IAM, côté serveur. Même si la décision reste consultative ici, le
     registre des quotas cesse de mentir sur ce que le SDK crée.
  2. UN REFUS TOT, AVEC SON MOTIF. « il vous reste 0 vCPU sur 4 » avant l appel
     au backend, plutôt qu une erreur générique après.
  3. LA SEQUENCE EN UN SEUL ENDROIT. décider → réserver → créer → confirmer, ou
     libérer si la création échoue. Recopiée dans chaque appelant, elle
     divergera — et c est le jour où elle divergera qu on comptera faux.

LE DEFAUT EST LE REFUS. Sans endpoint IAM configuré, la cellule lève
`CellUnavailable` et la création s arrête. Autoriser par défaut ferait de chaque
panne d IAM une levée générale des quotas.
"""

from __future__ import annotations

import math
from types import TracebackType
from typing import Any

from gandal_sdk.cells.iam import IamCell
from gandal_sdk.errors import GandalError

GIO = 1024**3


class DecisionRefusee(GandalError):
    """IAM a répondu « deny ». `motif` est le code du contrat."""

    def __init__(self, action: str, sujet: str, motif: str, explication: str) -> None:
        super().__init__(f"« {action} » refuse pour « {sujet} » : {motif} — {explication}")
        self.action, self.sujet = action, sujet
        self.motif, self.explication = motif, explication


class GardeIam:
    """La séquence, en un gestionnaire de contexte.

        with GardeIam(client.iam, sujet="etu-1", projet="p-vision") as g:
            g.autoriser_creation("poste-1", vcpu=2, ram_gb=4, disk_gb=20)
            demande = client.orchestration.vms.request_create(projet, corps)
            g.confirmer(demande.vm_id, "vm")

    Si le corps lève, la sortie **libère** la réservation : sans cela le quota
    reste retenu pour une VM qui n a jamais existé, et la personne est bloquée
    sans comprendre pourquoi.
    """

    def __init__(self, iam: IamCell, *, sujet: str, projet: str = "",
                 correlation_id: str | None = None) -> None:
        if not sujet:
            # Sans sujet, la décision porterait sur le service appelant, et tout
            # le monde pourrait ce que ce service peut.
            raise ValueError(
                "sujet obligatoire : sans lui la decision porterait sur le "
                "service appelant, donc tout le monde pourrait ce qu il peut")
        self.iam, self.sujet, self.projet = iam, sujet, projet
        self.correlation_id = correlation_id
        self.reservation: str = ""
        self._confirmee = False

    # ─── la question ────────────────────────────────────────────────────────

    def _ressource(self, type_: str, id_: str, **extra: Any) -> dict[str, Any]:
        r: dict[str, Any] = {"type": type_, "id": id_}
        if self.projet:
            r["projet"] = self.projet
        r.update({k: v for k, v in extra.items() if v is not None})
        return r

    def decider(self, action: str, ressource: dict[str, Any],
                contexte: dict[str, Any] | None = None) -> str:
        demande: dict[str, Any] = {"action": action, "ressource": ressource,
                                   "sujet_delegue": self.sujet}
        if contexte:
            demande["contexte"] = contexte
        d = self.iam.decide(demande, correlation_id=self.correlation_id)
        decision = getattr(d, "decision", None)
        if decision != "permit":
            raise DecisionRefusee(action, self.sujet,
                                  str(getattr(d, "motif", "") or ""),
                                  str(getattr(d, "explication", "") or ""))
        return str(getattr(d, "explication", "") or "")

    # ─── le quota ───────────────────────────────────────────────────────────

    def reserver(self, ressources: dict[str, int], *, duree_s: int = 900,
                 portee_ressource: str | None = None) -> str:
        r = self.iam.reserve_quota(
            ressources={k: v for k, v in ressources.items() if v},
            projet=self.projet or None, duree_s=duree_s,
            ressource_portee=portee_ressource, sujet_delegue=self.sujet,
            correlation_id=self.correlation_id)
        self.reservation = str(getattr(r, "id", "") or "")
        return self.reservation

    def confirmer(self, id_ressource: str, type_ressource: str = "vm") -> None:
        if not self.reservation:
            return
        self.iam.commit_reservation(self.reservation, ressource_id=id_ressource,
                                    ressource_type=type_ressource,
                                    correlation_id=self.correlation_id)
        self._confirmee = True

    def liberer(self) -> None:
        """Avale l échec : la réservation expirera seule, et faire échouer le
        nettoyage masquerait l erreur d origine — celle que l appelant doit voir."""
        if not self.reservation or self._confirmee:
            return
        try:
            self.iam.release_reservation(self.reservation,
                                         correlation_id=self.correlation_id)
        except Exception:                                  # noqa: BLE001
            pass
        finally:
            self.reservation = ""

    def rendre(self, id_ressource: str) -> None:
        """La ressource est détruite : son quota revient. Sans cet appel, le
        quota reste consommé par quelque chose qui n existe plus."""
        self.iam.release_resource(id_ressource, correlation_id=self.correlation_id)

    # ─── les VM ─────────────────────────────────────────────────────────────

    def autoriser_creation(self, nom: str, *, vcpu: int, ram_gb: int,
                           disk_gb: int, hote: str | None = None,
                           duree_s: int = 900) -> str:
        """Décide PUIS réserve, dans cet ordre. Réserver d abord retiendrait du
        quota pour une demande qui va être refusée."""
        motif = self.decider("vm:create", self._ressource("vm", nom, hote=hote),
                             {"vcpu": vcpu, "ram_gb": ram_gb, "disk_gb": disk_gb})
        self.reserver({"vm_count": 1, "vcpu": vcpu, "ram_gb": ram_gb,
                       "disk_gb": disk_gb}, duree_s=duree_s)
        return motif

    def autoriser_modification(self, id_vm: str, *, vcpu: int, ram_gb: int,
                               disk_gb: int) -> str:
        """Décide, **puis** redimensionne la ressource dans IAM.

        ELLE COMPTE MAINTENANT. Elle ne comptait pas : le coût du catalogue IAM
        *ajoute*, il ne retranche pas, donc compter un redimensionnement par le
        chemin des réservations aurait compté la taille **entière** au lieu de
        l écart — deux agrandissements de suite auraient compté deux fois la VM,
        et réduire une VM aurait laissé du quota consommé à vide.

        `POST /resources/{id}/resize` prend les quantités **absolues** et c est
        IAM qui soustrait, dans sa transaction. Lui faire porter l écart
        reviendrait à faire calculer par l appelant l arithmétique sur laquelle
        la décision repose.

        L ORDRE : décider d abord. Redimensionner avant de décider changerait le
        compteur pour une demande qui va être refusée.
        """
        motif = self.decider("vm:update", self._ressource("vm", id_vm),
                             {"vcpu": vcpu, "ram_gb": ram_gb, "disk_gb": disk_gb})
        self.redimensionner(id_vm, {"vcpu": vcpu, "ram_gb": ram_gb,
                                    "disk_gb": disk_gb})
        return motif

    def redimensionner(self, id_ressource: str, quantites: dict[str, int]) -> None:
        """Quantités **absolues**, IAM soustrait. Les clés absentes restent
        inchangées : un appelant qui ne parle que de la mémoire ne doit pas
        effacer le compte de vCPU au passage."""
        self.iam.resize_resource(id_ressource, quantites,
                                 correlation_id=self.correlation_id)

    def autoriser_suppression(self, id_vm: str) -> str:
        return self.decider("vm:delete", self._ressource("vm", id_vm))

    def autoriser_alimentation(self, id_vm: str, action: str) -> str:
        """`start` | `stop` | `reboot`. Un redémarrage est un arrêt suivi d un
        démarrage : on exige `vm:stop`, la plus forte des deux."""
        actions = {"start": "vm:start", "stop": "vm:stop", "reboot": "vm:stop"}
        if action not in actions:
            raise ValueError(f"action d alimentation inconnue : « {action} »")
        return self.decider(actions[action], self._ressource("vm", id_vm))

    # ─── le stockage objet : Drive, S3, Supabase ─────────────────────────────
    #
    # UN PROJET SANS QUOTA DE STOCKAGE EST REFUSE, et c est le défaut côté IAM :
    # la limite par défaut d un projet est zéro. Accorder le quota active le
    # stockage, le ramener à zéro le retire. Il n y a rien d autre à brancher
    # pour que « ce projet utilise le stockage, celui-là non » soit vrai.
    #
    # QUEL FOURNISSEUR est un ATTRIBUT du projet (`stockage-fournisseur`), pas un
    # quota : « s3 » n est pas une quantité.

    def autoriser_creation_seau(self, nom: str, *, fournisseur: str | None = None,
                                duree_s: int = 300) -> str:
        motif = self.decider("storage:bucket:create",
                             self._ressource("bucket", nom, fournisseur=fournisseur))
        self.reserver({"storage_buckets": 1}, duree_s=duree_s)
        return motif

    def autoriser_suppression_seau(self, nom: str) -> str:
        return self.decider("storage:bucket:delete", self._ressource("bucket", nom))

    def autoriser_ecriture(self, seau: str, cle: str, *, octets: int,
                           duree_s: int = 300) -> str:
        """Arrondi au Gio SUPERIEUR : facturer 0 Gio pour un fichier de 1 Mio
        laisserait passer un million de fichiers sans rien compter."""
        gio = max(1, math.ceil(octets / GIO)) if octets > 0 else 0
        motif = self.decider("storage:object:write",
                             self._ressource("objet", f"{seau}/{cle}", seau=seau),
                             {"storage_gb": gio})
        if gio:
            self.reserver({"storage_gb": gio, "storage_objects": 1},
                          duree_s=duree_s, portee_ressource=seau)
        return motif

    def autoriser_lecture(self, seau: str, cle: str, *, octets: int) -> str:
        """Compte la SORTIE au quota mensuel : c est l axe qui se facture, et le
        seul qu une boucle peut faire exploser en une nuit."""
        gio = max(1, math.ceil(octets / GIO)) if octets > 0 else 0
        motif = self.decider("storage:object:read",
                             self._ressource("objet", f"{seau}/{cle}", seau=seau),
                             {"storage_egress_gb_month": gio})
        if gio:
            # Ressource de PERIODE : elle se consomme et ne se rend pas. On
            # réserve et on confirme tout de suite, sur le seau.
            self.reserver({"storage_egress_gb_month": gio}, duree_s=60,
                          portee_ressource=seau)
            self.confirmer(seau, "bucket")
        return motif

    # ─── sortie ─────────────────────────────────────────────────────────────

    def __enter__(self) -> "GardeIam":
        return self

    def __exit__(self, type_exc: type[BaseException] | None,
                 _valeur: BaseException | None,
                 _trace: TracebackType | None) -> None:
        if type_exc is not None:
            self.liberer()
