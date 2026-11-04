"""La garde IAM du SDK : la sequence, et surtout ses sorties de secours."""

from __future__ import annotations

import pytest

from gandal_sdk.garde import DecisionRefusee, GardeIam


class FauxIam:
    """Cellule IAM d essai. Journalise tout, et sait refuser sur commande."""

    def __init__(self, decision: str = "permit", lever_reservation: bool = False) -> None:
        self.decision, self.lever_reservation = decision, lever_reservation
        self.journal: list[tuple[str, dict]] = []

    class _D:
        def __init__(self, decision, motif="", explication=""):
            self.decision, self.motif, self.explication = decision, motif, explication

    class _R:
        def __init__(self, id_):
            self.id = id_

    def decide(self, demande, *, correlation_id=None):
        self.journal.append(("decide", dict(demande)))
        if self.decision == "permit":
            return self._D("permit", explication="quota du projet : 2 vCPU restants")
        return self._D("deny", motif="quota", explication="il vous reste 0 vCPU sur 4")

    def reserve_quota(self, **kw):
        self.journal.append(("reserve", kw))
        if self.lever_reservation:
            raise RuntimeError("quota epuise cote serveur")
        return self._R("res-1")

    def commit_reservation(self, reservation_id, **kw):
        self.journal.append(("commit", {"id": reservation_id, **kw}))
        return self._R(reservation_id)

    def release_reservation(self, reservation_id, **kw):
        self.journal.append(("release_reservation", {"id": reservation_id}))

    def release_resource(self, resource_id, **kw):
        self.journal.append(("release_resource", {"id": resource_id}))

    def etapes(self) -> list[str]:
        return [nom for nom, _ in self.journal]


# ─── la sequence ────────────────────────────────────────────────────────────

def test_creation_decide_puis_reserve_puis_confirme():
    iam = FauxIam()
    with GardeIam(iam, sujet="etu-1", projet="p-vision") as g:
        g.autoriser_creation("poste-1", vcpu=2, ram_gb=4, disk_gb=20, hote="emilia")
        g.confirmer("poste-1", "vm")
    assert iam.etapes() == ["decide", "reserve", "commit"]
    _, d = iam.journal[0]
    # La decision porte sur la PERSONNE, pas sur le service appelant.
    assert d["sujet_delegue"] == "etu-1"
    assert d["ressource"] == {"type": "vm", "id": "poste-1",
                              "projet": "p-vision", "hote": "emilia"}
    assert d["contexte"] == {"vcpu": 2, "ram_gb": 4, "disk_gb": 20}
    _, r = iam.journal[1]
    assert r["ressources"] == {"vm_count": 1, "vcpu": 2, "ram_gb": 4, "disk_gb": 20}


def test_decider_avant_reserver_et_pas_l_inverse():
    """Reserver d abord retiendrait du quota pour une demande deja refusee."""
    iam = FauxIam(decision="deny")
    with pytest.raises(DecisionRefusee):
        with GardeIam(iam, sujet="etu-1") as g:
            g.autoriser_creation("poste-2", vcpu=99, ram_gb=99, disk_gb=99)
    assert iam.etapes() == ["decide"]


def test_le_refus_porte_le_motif_et_la_phrase_d_iam():
    iam = FauxIam(decision="deny")
    with pytest.raises(DecisionRefusee) as exc:
        GardeIam(iam, sujet="etu-1").autoriser_suppression("poste-1")
    assert exc.value.motif == "quota"
    assert "0 vCPU sur 4" in exc.value.explication
    assert "vm:delete" in str(exc.value)


# ─── les deux fautes qui ne se voient pas ───────────────────────────────────

def test_si_la_creation_leve_le_quota_est_rendu():
    iam = FauxIam()
    with pytest.raises(RuntimeError):
        with GardeIam(iam, sujet="etu-1") as g:
            g.autoriser_creation("poste-3", vcpu=2, ram_gb=4, disk_gb=20)
            raise RuntimeError("le backend a refuse")
    assert iam.etapes() == ["decide", "reserve", "release_reservation"]
    assert "commit" not in iam.etapes()


def test_une_reservation_confirmee_n_est_pas_liberee():
    iam = FauxIam()
    with GardeIam(iam, sujet="etu-1") as g:
        g.autoriser_creation("poste-4", vcpu=1, ram_gb=1, disk_gb=10)
        g.confirmer("poste-4", "vm")
    assert "release_reservation" not in iam.etapes()


def test_liberer_avale_son_echec_pour_ne_pas_masquer_l_erreur_d_origine():
    """L appelant doit voir « le backend a refuse », pas « la liberation a echoue »."""
    iam = FauxIam()

    def tombe(reservation_id, **kw):
        raise RuntimeError("IAM injoignable pendant le nettoyage")

    iam.release_reservation = tombe  # type: ignore[assignment]
    with pytest.raises(RuntimeError, match="le backend a refuse"):
        with GardeIam(iam, sujet="etu-1") as g:
            g.autoriser_creation("poste-5", vcpu=1, ram_gb=1, disk_gb=10)
            raise RuntimeError("le backend a refuse")


def test_sans_sujet_on_refuse():
    """Sans sujet, la decision porterait sur le service appelant."""
    with pytest.raises(ValueError, match="sujet obligatoire"):
        GardeIam(FauxIam(), sujet="")


# ─── vm:update decide mais ne compte pas, et c est volontaire ───────────────

def test_modification_decide_sans_toucher_au_quota():
    iam = FauxIam()
    g = GardeIam(iam, sujet="etu-1", projet="p-vision")
    g.autoriser_modification("poste-1", vcpu=4, ram_gb=8, disk_gb=40)
    assert iam.etapes() == ["decide"]
    assert iam.journal[0][1]["action"] == "vm:update"


def test_reboot_exige_la_plus_forte_des_deux():
    iam = FauxIam()
    g = GardeIam(iam, sujet="etu-1")
    g.autoriser_alimentation("poste-1", "reboot")
    assert iam.journal[0][1]["action"] == "vm:stop"
    with pytest.raises(ValueError, match="inconnue"):
        g.autoriser_alimentation("poste-1", "exploser")


# ─── le stockage : Drive, S3, Supabase ──────────────────────────────────────

def test_un_objet_de_un_octet_compte_un_gio_jamais_zero():
    """Facturer 0 Gio laisserait passer un million de fichiers sans rien compter."""
    iam = FauxIam()
    g = GardeIam(iam, sujet="etu-1", projet="p-vision")
    g.autoriser_ecriture("donnees", "image.tif", octets=1)
    _, r = next(x for x in iam.journal if x[0] == "reserve")
    assert r["ressources"] == {"storage_gb": 1, "storage_objects": 1}
    # Le quota compte CONTRE LE SEAU : c est la portee « ressource ».
    assert r["ressource_portee"] == "donnees"


def test_un_objet_vide_ne_reserve_rien():
    iam = FauxIam()
    GardeIam(iam, sujet="etu-1").autoriser_ecriture("d", "vide", octets=0)
    assert iam.etapes() == ["decide"]


def test_la_lecture_compte_la_sortie_et_la_confirme_tout_de_suite():
    """Une ressource de periode se consomme et ne se rend pas."""
    iam = FauxIam()
    g = GardeIam(iam, sujet="etu-1", projet="p-vision")
    g.autoriser_lecture("donnees", "image.tif", octets=3 * 1024**3)
    _, r = next(x for x in iam.journal if x[0] == "reserve")
    assert r["ressources"] == {"storage_egress_gb_month": 3}
    assert "commit" in iam.etapes()


def test_le_fournisseur_voyage_dans_la_ressource_pas_dans_un_quota():
    """« s3 » n est pas une quantite : c est un attribut, lisible par une politique."""
    iam = FauxIam()
    g = GardeIam(iam, sujet="etu-1", projet="p-vision")
    g.autoriser_creation_seau("seau-s3", fournisseur="s3")
    _, d = iam.journal[0]
    assert d["ressource"]["fournisseur"] == "s3"
    assert d["ressource"]["projet"] == "p-vision"
    assert d["action"] == "storage:bucket:create"


def test_un_projet_sans_quota_de_stockage_est_refuse_par_le_quota():
    """Il n y a pas d interrupteur separe : la porte EST le quota, a zero."""
    iam = FauxIam(lever_reservation=True)
    with pytest.raises(RuntimeError, match="quota epuise"):
        with GardeIam(iam, sujet="etu-1", projet="p-sans-stockage") as g:
            g.autoriser_creation_seau("jeux")
    assert iam.etapes() == ["decide", "reserve"]


def test_rendre_libere_le_quota_d_une_ressource_detruite():
    iam = FauxIam()
    GardeIam(iam, sujet="etu-1").rendre("poste-1")
    assert iam.journal == [("release_resource", {"id": "poste-1"})]
