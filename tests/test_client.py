"""GandalClient : login, me, stubs cellules."""

import pytest
import respx

from gandal_sdk import CellUnavailable, GandalClient


@respx.mock
def test_login_stores_token_and_me_works() -> None:
    """login conserve le Bearer ; me lit /auth/me."""
    respx.post("http://example.test/api/v1/auth/login").respond(
        200,
        json={"access_token": "abc", "token_type": "bearer", "expires_in": 3600},
    )
    me_route = respx.get("http://example.test/api/v1/auth/me").respond(
        200,
        json={
            "user_id": "u1",
            "email": "alice@iaas.cm",
            "first_name": "Alice",
            "last_name": "A",
            "role": "user",
        },
    )
    with GandalClient("http://example.test") as client:
        token = client.login("alice@iaas.cm", "alice123")
        assert token.access_token == "abc"
        identity = client.me()
        assert identity.email == "alice@iaas.cm"
        assert me_route.calls[0].request.headers["Authorization"] == "Bearer abc"


@respx.mock
def test_orchestration_health() -> None:
    """health() appelle /api/v1/health."""
    respx.get("http://example.test/api/v1/health").respond(200, json={"status": "ok"})
    with GandalClient("http://example.test") as client:
        assert client.orchestration.health().status == "ok"


@respx.mock
def test_orchestration_generic_get_prefixes_api_v1() -> None:
    """get('/projects') vise /api/v1/projects."""
    respx.get("http://example.test/api/v1/projects").respond(200, json={"items": []})
    with GandalClient("http://example.test") as client:
        assert client.orchestration.get("/projects") == {"items": []}


def test_cell_stubs_raise_unavailable() -> None:
    """Chaque cellule sans endpoint leve CellUnavailable."""
    with GandalClient("http://example.test") as client:
        with pytest.raises(CellUnavailable):
            client.iam.get_me()
        with pytest.raises(CellUnavailable):
            from gandal_sdk.cells.hypervisor import VmSpec

            client.hypervisor.create_vm(
                VmSpec(name="v", ram_gb=1, vcpu=1, vram_gb=0, ssd_gb=10)
            )
        with pytest.raises(CellUnavailable):
            client.network.create_network("p1", "net")
        with pytest.raises(CellUnavailable):
            from gandal_sdk.cells.storage import StorageSpec

            client.storage.create_storage(StorageSpec(name="s", size_gb=10))
        with pytest.raises(CellUnavailable):
            client.dns.delete_domain("vm-1")
        with pytest.raises(CellUnavailable):
            from gandal_sdk.cells.notifications import Notification

            client.notifications.notify(
                Notification(user_id="u", subject="s", message="m")
            )
