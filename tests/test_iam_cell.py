"""Client de la cellule IAM, sur des reponses alignees au contrat 1.7.0."""

from __future__ import annotations

import pytest
import respx

from gandal_sdk import CellUnavailable, GandalApiError, GandalClient
from gandal_sdk.cells.iam import (
    Capacite,
    DecisionMotif,
    DecisionVerdict,
    DemandeDecision,
    DemandeRessource,
)

CELL = "https://iam.test/v1"


def _sujet(**overrides: object) -> dict:
    base = {
        "id": "sub_01",
        "identifiant": "alice",
        "courriel": "alice@gandal.test",
        "actif": True,
        "externe": False,
        "expire_a": None,
        "roles": [{"nom": "user"}],
        "groupes": ["promotion-gi27"],
        "attributs": {"vm_count": "1"},
        "correlation_id": "01JB9X2K7M4Q8V0ZC3N5T6R7W8",
    }
    base.update(overrides)
    return base


def _decision(verdict: str = "permit", motif: str = "capacite_projet") -> dict:
    return {
        "decision": verdict,
        "motif": motif,
        "explication": "ok",
        "regle": "Q-001",
        "valide_jusqu_a": "2026-11-04T12:00:00Z",
        "obligations": [],
        "correlation_id": "01JB9X2K7M4Q8V0ZC3N5T6R7W8",
    }


@pytest.fixture
def client():
    with GandalClient(
        "http://api.test",
        cell_urls={"iam": CELL},
        cell_tokens={"iam": "jeton-iam"},
        cell_verify={"iam": False},
    ) as gandal:
        yield gandal


def test_unconfigured_cell_is_unavailable() -> None:
    with GandalClient("http://api.test") as client:
        with pytest.raises(CellUnavailable):
            client.iam.list_subjects()


@respx.mock
def test_decide_sends_bearer_and_body(client: GandalClient) -> None:
    route = respx.post(f"{CELL}/decisions").respond(200, json=_decision())
    decision = client.iam.decide(
        DemandeDecision(
            action="vm:create",
            ressource=DemandeRessource(type="vm", projet="prj_01"),
        )
    )
    assert decision.decision == DecisionVerdict.PERMIT
    assert decision.motif == DecisionMotif.CAPACITE_PROJET
    request = route.calls.last.request
    assert request.headers["Authorization"] == "Bearer jeton-iam"
    assert b'"vm:create"' in request.read()


@respx.mock
def test_create_project_sends_idempotency_key(client: GandalClient) -> None:
    projet = {
        "id": "prj_01",
        "nom": "tp",
        "proprietaire": "sub_01",
        "etat": "actif",
        "correlation_id": "01JB9X2K7M4Q8V0ZC3N5T6R7W8",
    }
    route = respx.post(f"{CELL}/projects").respond(201, json=projet)
    created = client.iam.create_project(nom="tp", idempotency_key="cle-fixe-12345678")
    assert created.id == "prj_01"
    assert route.calls.last.request.headers["Idempotency-Key"] == "cle-fixe-12345678"


@respx.mock
def test_create_access_key_has_no_idempotency_key(client: GandalClient) -> None:
    """Le secret ne doit pas etre rejoue via Idempotency-Key (contrat famille F)."""
    route = respx.post(f"{CELL}/access-keys").respond(
        201, json={"id": "key_01", "secret": "sekrit"}
    )
    out = client.iam.create_access_key({"description": "ci"})
    assert out["secret"] == "sekrit"
    assert "Idempotency-Key" not in route.calls.last.request.headers


@respx.mock
def test_subjects_me_and_invite_member(client: GandalClient) -> None:
    respx.get(f"{CELL}/subjects/me").respond(200, json=_sujet())
    respx.post(f"{CELL}/projects/prj_01/members").respond(
        201,
        json={
            "sujet": "sub_02",
            "capacite": "contributeur",
            "identifiant": "bob",
        },
    )
    me = client.iam.get_me()
    assert me.identifiant == "alice"
    member = client.iam.invite_member(
        "prj_01", sujet="sub_02", capacite=Capacite.CONTRIBUTEUR
    )
    assert member.capacite == Capacite.CONTRIBUTEUR


@respx.mock
def test_quota_reserve_commit_release(client: GandalClient) -> None:
    reservation = {
        "id": "res_01",
        "sujet": "sub_01",
        "projet": "prj_01",
        "ressources": {"vm_count": 1},
        "etat": "reservee",
        "expire_a": "2026-11-04T12:30:00Z",
        "ressource_id": None,
        "correlation_id": "01JB9X2K7M4Q8V0ZC3N5T6R7W8",
    }
    respx.post(f"{CELL}/quota-reservations").respond(201, json=reservation)
    confirmed = {**reservation, "etat": "confirmee", "ressource_id": "vm-9"}
    respx.post(f"{CELL}/quota-reservations/res_01/commit").respond(200, json=confirmed)
    respx.post(f"{CELL}/resources/vm-9/release").respond(
        200,
        json={
            "portee": "projet",
            "projet": "prj_01",
            "limites": [
                {
                    "ressource": "vm_count",
                    "nature": "stock",
                    "limite": 1,
                    "consomme": 0,
                    "reserve": 0,
                    "restant": 1,
                }
            ],
            "correlation_id": "01JB9X2K7M4Q8V0ZC3N5T6R7W8",
        },
    )

    reserved = client.iam.reserve_quota(ressources={"vm_count": 1}, projet="prj_01")
    assert reserved.etat.value == "reservee"
    done = client.iam.commit_reservation("res_01", ressource_id="vm-9")
    assert done.ressource_id == "vm-9"
    quotas = client.iam.release_resource("vm-9")
    assert quotas.limites[0].restant == 1


@respx.mock
def test_problem_json_mapped_to_api_error(client: GandalClient) -> None:
    respx.get(f"{CELL}/subjects/absent").respond(
        404,
        headers={"content-type": "application/problem+json"},
        json={
            "type": "https://gandal.local/problems/introuvable",
            "title": "Introuvable",
            "status": 404,
            "detail": "sujet inconnu",
            "correlation_id": "01JB9X2K7M4Q8V0ZC3N5T6R7W8",
        },
    )
    with pytest.raises(GandalApiError) as caught:
        client.iam.get_subject("absent")
    assert caught.value.code == "introuvable"
    assert caught.value.message == "sujet inconnu"
    assert caught.value.status == 404
    assert caught.value.details["correlation_id"] == "01JB9X2K7M4Q8V0ZC3N5T6R7W8"


@respx.mock
def test_oidc_discovery_and_whoami(client: GandalClient) -> None:
    respx.get(f"{CELL}/.well-known/openid-configuration").respond(
        200, json={"issuer": "https://idp.test/realms/gandal"}
    )
    respx.get(f"{CELL}/protocol/openid-connect/certs").respond(
        200, json={"keys": []}
    )
    respx.get(f"{CELL}/sts/whoami").respond(200, json={"sujet": "sub_01", "roles": []})
    assert client.iam.openid_configuration()["issuer"].endswith("/gandal")
    assert client.iam.jwks() == {"keys": []}
    assert client.iam.whoami()["sujet"] == "sub_01"


@respx.mock
def test_policies_and_tags_roundtrip(client: GandalClient) -> None:
    respx.post(f"{CELL}/policies").respond(201, json={"nom": "deny-prod"})
    respx.post(f"{CELL}/policies/deny-prod/attachments").respond(201, json={})
    respx.patch(f"{CELL}/tags/sujet/sub_01").respond(200, json={"attributs": {"env": "lab"}})
    assert client.iam.create_policy(
        {"nom": "deny-prod", "document": {"Version": "2026-11-01", "Statement": []}}
    )["nom"] == "deny-prod"
    client.iam.attach_policy("deny-prod", {"cible_type": "organisation"})
    tags = client.iam.set_tags("sujet", "sub_01", {"attributs": {"env": "lab"}})
    assert tags["attributs"]["env"] == "lab"


@respx.mock
def test_from_env_configures_iam_cell(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "credentials"
    path.write_text(
        "[default]\nendpoint = http://api.test\n"
        "iam_endpoint = http://iam-fichier.test/v1\niam_token = jeton-fichier\n"
    )
    monkeypatch.setenv("GANDAL_CREDENTIALS_FILE", str(path))
    for name in (
        "GANDAL_ENDPOINT",
        "GANDAL_TOKEN",
        "GANDAL_PROFILE",
        "GANDAL_IAM_ENDPOINT",
        "GANDAL_IAM_TOKEN",
        "GANDAL_IAM_CA",
    ):
        monkeypatch.delenv(name, raising=False)
    route = respx.get("http://iam-fichier.test/v1/subjects/me").respond(200, json=_sujet())
    with GandalClient.from_env() as client:
        assert client.iam.get_me().id == "sub_01"
    assert route.calls.last.request.headers["Authorization"] == "Bearer jeton-fichier"
