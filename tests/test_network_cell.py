"""Client de la cellule reseau (agent_reseau), sur des reponses d'enveloppe d'execution."""

from __future__ import annotations

import pytest
import respx

from gandal_sdk import CellUnavailable, GandalApiError, GandalClient, GandalError
from gandal_sdk.cells.network import NetworkMode, NetworkRef

CELL = "http://network.test"


def _execution(
    *,
    state: str = "SUCCEEDED",
    operation: str = "network.xcpng.networks",
    data: dict | None = None,
    execution_id: int = 42,
) -> dict:
    return {
        "execution_id": execution_id,
        "operation": operation,
        "state": state,
        "result": {"returncode": 0 if state == "SUCCEEDED" else 1, "data": data or {}},
        "replay": False,
        "links": {"self": f"/v1/executions/{execution_id}"},
    }


@pytest.fixture
def client():
    with GandalClient(
        "http://api.test",
        cell_urls={"network": CELL},
        cell_tokens={"network": "jeton-agent"},
    ) as gandal:
        yield gandal


def test_unconfigured_cell_is_unavailable() -> None:
    with GandalClient("http://api.test") as bare:
        with pytest.raises(CellUnavailable):
            bare.network.health()


@respx.mock
def test_health_without_auth_header_ok(client: GandalClient) -> None:
    respx.get(f"{CELL}/v1/health").respond(200, json={"status": "ok"})
    assert client.network.health() == {"status": "ok"}


@respx.mock
def test_run_sends_standard_body_and_bearer(client: GandalClient) -> None:
    route = respx.post(f"{CELL}/v1/xcpng/networks").respond(
        200, json=_execution(data={"changed": True, "verified": True})
    )
    exe = client.network.create_network(
        target_id="cluster-lab",
        resource_key="request-a",
        name="Projet A",
        mtu=1500,
        mode=NetworkMode.CHECK,
    )
    assert exe.succeeded
    assert exe.execution_id == 42
    request = route.calls.last.request
    assert request.headers["Authorization"] == "Bearer jeton-agent"
    body = request.read()
    assert b'"action":"create_internal"' in body
    assert b'"mode":"check"' in body
    assert b'"target_id":"cluster-lab"' in body


@respx.mock
def test_attach_vm_uses_vm_networks_add(client: GandalClient) -> None:
    route = respx.post(f"{CELL}/v1/vm-networks").respond(
        200, json=_execution(operation="network.vm-networks")
    )
    client.network.attach_vm(
        NetworkRef(network_id="11111111-1111-4111-8111-111111111111"),
        "33333333-3333-4333-8333-333333333333",
        target_id="cluster-lab",
        resource_key="request-a",
        user_uuid="55555555-5555-4555-8555-555555555555",
        hostname="vm.projects.example.",
        mode="apply",
    )
    body = route.calls.last.request.read()
    assert b'"action":"add"' in body
    assert b'"mode":"apply"' in body


@respx.mock
def test_user_vms_shortcut(client: GandalClient) -> None:
    respx.post(f"{CELL}/v1/user-vms").respond(
        200, json=_execution(operation="network.user-vms", data={"state": "ATTACHED"})
    )
    exe = client.network.user_vms(
        "deploy",
        {
            "user_uuid": "11111111-1111-4111-8111-111111111111",
            "project_uuid": "22222222-2222-4222-8222-222222222222",
            "project_name": "boutique",
            "vm_uuid": "33333333-3333-4333-8333-333333333333",
        },
        target_id="cluster-prod",
        mode=NetworkMode.APPLY,
    )
    assert exe.data["state"] == "ATTACHED"


@respx.mock
def test_failed_execution_body_is_still_parsed(client: GandalClient) -> None:
    """L'agent renvoie 502 + enveloppe ; le SDK expose NetworkExecution."""
    respx.post(f"{CELL}/v1/xcpng/networks").respond(
        502,
        json=_execution(state="FAILED", data={"error": "Conflict", "code": "Conflict"}),
    )
    exe = client.network.create_network(
        target_id="cluster-lab",
        resource_key="request-a",
        name="Projet A",
        mode="apply",
    )
    assert exe.state == "FAILED"
    with pytest.raises(GandalError, match="FAILED"):
        client.network.require_succeeded(exe)


@respx.mock
def test_agent_string_error_becomes_api_error(client: GandalClient) -> None:
    respx.post(f"{CELL}/v1/flows").respond(401, json={"error": "authentification requise"})
    with pytest.raises(GandalApiError, match="authentification requise") as caught:
        client.network.flows("list", {}, target_id="cluster-lab")
    assert caught.value.status == 401


def test_detach_vm_from_project_explains_gap(client: GandalClient) -> None:
    with pytest.raises(GandalError, match="pas d'operation unique"):
        client.network.detach_vm_from_project("vm-1", "prj_1")


@respx.mock
def test_get_execution(client: GandalClient) -> None:
    respx.get(f"{CELL}/v1/executions/7").respond(200, json=_execution(execution_id=7))
    assert client.network.get_execution(7).execution_id == 7
