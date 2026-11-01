"""Waiters des demandes et des stockages contre une API simulee."""

import httpx
import pytest
import respx

from gandal_sdk import GandalClient
from gandal_sdk.waiters import WaiterFailure

REQUEST_URL = "http://example.test/api/v1/requests/12"
STORAGE_URL = "http://example.test/api/v1/projects/prj-1/storages/st-1"
NOT_FOUND = {"error": {"code": "not_found", "message": "absent", "details": None}}


def _request(status: str, note: str | None = None, target: str | None = None) -> httpx.Response:
    """Reponse GET d'une demande de creation de VM."""
    return httpx.Response(
        200,
        json={
            "id": 12,
            "project_id": "prj-1",
            "author_id": "usr-1",
            "kind": "vm_create",
            "status": status,
            "payload": {"name": "web-01"},
            "target_resource_type": "vm" if target else None,
            "target_resource_id": target,
            "admin_note": note,
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
            "decided_at": None if status == "pending" else "2026-01-01T01:00:00Z",
        },
    )


@pytest.fixture
def client():
    """Client dont les attentes sont enregistrees, sans dormir."""
    with GandalClient("http://example.test") as gandal:
        gandal.sleeps = []
        gandal._http.sleep = gandal.sleeps.append
        yield gandal


@respx.mock
def test_wait_until_accepted_returns_created_resource(client) -> None:
    """pending puis accepted : la demande renvoyee designe la VM creee."""
    respx.get(REQUEST_URL).mock(
        side_effect=[_request("pending"), _request("accepted", target="vm-9")]
    )
    request = client.orchestration.requests.wait_until_accepted(12)
    assert request.target_resource_id == "vm-9"
    assert client.sleeps == [15.0]


@respx.mock
def test_wait_until_accepted_fails_on_refusal_with_admin_note(client) -> None:
    """Un refus arrete l'attente et cite la note de l'administrateur."""
    respx.get(REQUEST_URL).mock(return_value=_request("refused", note="quota atteint"))
    with pytest.raises(WaiterFailure, match=r"refused \(quota atteint\)"):
        client.orchestration.requests.wait_until_accepted(12)


@respx.mock
def test_wait_until_accepted_fails_on_cancellation(client) -> None:
    """Une demande annulee ne sera jamais acceptee."""
    respx.get(REQUEST_URL).mock(return_value=_request("cancelled"))
    with pytest.raises(WaiterFailure, match="cancelled"):
        client.orchestration.requests.wait_until_accepted(12)


@respx.mock
def test_storage_wait_until_deleted_ends_on_404(client) -> None:
    """deleting puis 404 : le stockage est supprime."""
    deleting = {
        "id": "st-1",
        "origin_project_id": "prj-1",
        "name": "backup",
        "ip_address": None,
        "size_gb": 50,
        "state": "deleting",
        "created_at": "2026-01-01T00:00:00Z",
    }
    respx.get(STORAGE_URL).mock(
        side_effect=[httpx.Response(200, json=deleting), httpx.Response(404, json=NOT_FOUND)]
    )
    assert client.orchestration.storages.wait_until_deleted("prj-1", "st-1") is None
    assert len(client.sleeps) == 1
