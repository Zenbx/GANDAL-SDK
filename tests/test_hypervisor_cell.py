"""Client de la cellule hyperviseur, sur des reponses relevees sur gandal-hypervisor."""

import httpx
import pytest
import respx

from gandal_sdk import CellUnavailable, GandalApiError, GandalClient, WaiterFailure
from gandal_sdk.cells.hypervisor import OperationStatus, PowerAction, VmSpec
from gandal_sdk.orchestration.enums import VmState

CELL = "http://cell.test"
SPEC = VmSpec(name="sdk-it-a", ram_gb=1, vcpu=1, vram_gb=0, ssd_gb=10)


def _vm(state: str, ip: str | None = None) -> dict:
    return {
        "vm_id": "vm-9a6bd88b3c5f",
        "name": "sdk-it-a",
        "state": state,
        "ip_address": ip,
        "ram_gb": 1,
        "vcpu": 1,
        "ssd_gb": 10,
        "host": "emilia" if state == "running" else None,
        "xapi_uuid": "e80f86e8-4ccf-4f6b-9840-16fa258dcbf4",
    }


def _op(status: str, error: dict | None = None, action: str = "vm.create") -> dict:
    return {
        "id": "op-3e6eb5c4357c",
        "action": action,
        "vm_id": "vm-9a6bd88b3c5f",
        "status": status,
        "error": error,
        "created_at": "2026-11-01T07:12:30.976509Z",
        "updated_at": "2026-11-01T07:12:30.977093Z",
    }


@pytest.fixture
def client():
    with GandalClient(
        "http://api.test",
        cell_urls={"hypervisor": CELL},
        cell_tokens={"hypervisor": "jeton-cellule"},
    ) as gandal:
        gandal.hypervisor._http.sleep = lambda _: None
        yield gandal


def test_unconfigured_cell_is_unavailable() -> None:
    with GandalClient("http://api.test") as client:
        with pytest.raises(CellUnavailable):
            client.hypervisor.list_vms()


@respx.mock
def test_create_sends_spec_with_cell_token(client: GandalClient) -> None:
    route = respx.post(f"{CELL}/v1/vms").respond(
        202, json={"vm": _vm("creating"), "operation": _op("pending")}
    )
    created = client.hypervisor.create_vm(SPEC)
    assert created.vm.state == VmState.CREATING
    assert created.operation.status == OperationStatus.PENDING
    request = route.calls.last.request
    assert request.headers["Authorization"] == "Bearer jeton-cellule"
    assert request.read() == (b'{"name":"sdk-it-a","ram_gb":1,"vcpu":1,"vram_gb":0,"ssd_gb":10}')


@respx.mock
def test_full_flow_with_waiters(client: GandalClient) -> None:
    respx.post(f"{CELL}/v1/vms").respond(
        202, json={"vm": _vm("creating"), "operation": _op("pending")}
    )
    respx.get(f"{CELL}/v1/operations/op-3e6eb5c4357c").mock(
        side_effect=[
            httpx.Response(200, json=_op("running")),
            httpx.Response(200, json=_op("succeeded")),
        ]
    )
    respx.get(f"{CELL}/v1/vms/vm-9a6bd88b3c5f").respond(200, json=_vm("running", "10.10.0.11"))

    created = client.hypervisor.create_vm(SPEC)
    assert (
        client.hypervisor.wait_for_operation(created.operation).status == OperationStatus.SUCCEEDED
    )
    vm = client.hypervisor.wait_until_running(created.vm)
    assert (vm.ip_address, vm.host) == ("10.10.0.11", "emilia")
    assert vm.ref.vm_id == "vm-9a6bd88b3c5f"


@respx.mock
def test_failed_operation_reports_cell_error(client: GandalClient) -> None:
    error = {
        "code": "internal_error",
        "message": "Echec XAPI : HOST_NOT_ENOUGH_FREE_MEMORY",
        "details": {"xapi": ["HOST_NOT_ENOUGH_FREE_MEMORY", "1", "0"]},
    }
    respx.get(f"{CELL}/v1/operations/op-3e6eb5c4357c").respond(200, json=_op("failed", error))
    with pytest.raises(WaiterFailure, match="HOST_NOT_ENOUGH_FREE_MEMORY") as caught:
        client.hypervisor.wait_for_operation("op-3e6eb5c4357c")
    assert caught.value.last_value.error.details["xapi"][0] == "HOST_NOT_ENOUGH_FREE_MEMORY"


@respx.mock
def test_vm_in_error_stops_running_waiter(client: GandalClient) -> None:
    respx.get(f"{CELL}/v1/vms/vm-9a6bd88b3c5f").respond(200, json=_vm("error"))
    with pytest.raises(WaiterFailure, match="etat error"):
        client.hypervisor.wait_until_running("vm-9a6bd88b3c5f")


@respx.mock
def test_power_update_delete_return_operations(client: GandalClient) -> None:
    for method, path, action in (
        ("post", "/power", "vm.stop"),
        ("put", "", "vm.update"),
        ("delete", "", "vm.delete"),
    ):
        getattr(respx, method)(f"{CELL}/v1/vms/vm-9a6bd88b3c5f{path}").respond(
            202, json={"operation": _op("pending", action=action)}
        )
    stop = client.hypervisor.power("vm-9a6bd88b3c5f", PowerAction.STOP)
    assert respx.calls.last.request.read() == b'{"action":"stop"}'
    assert stop.action == "vm.stop"
    assert client.hypervisor.update_vm("vm-9a6bd88b3c5f", SPEC).action == "vm.update"
    assert client.hypervisor.delete_vm("vm-9a6bd88b3c5f").action == "vm.delete"


@respx.mock
def test_deleted_waiter_ends_on_404_envelope(client: GandalClient) -> None:
    respx.get(f"{CELL}/v1/vms/vm-9a6bd88b3c5f").mock(
        side_effect=[
            httpx.Response(200, json=_vm("deleting")),
            httpx.Response(
                404,
                json={
                    "error": {"code": "not_found", "message": "VM introuvable.", "details": None}
                },
            ),
        ]
    )
    assert client.hypervisor.wait_until_deleted("vm-9a6bd88b3c5f") is None


@respx.mock
def test_console_not_implemented_is_explicit(client: GandalClient) -> None:
    respx.post(f"{CELL}/v1/vms/vm-9a6bd88b3c5f/console").respond(
        501,
        json={
            "error": {
                "code": "not_implemented",
                "message": "Console non disponible.",
                "details": None,
            }
        },
    )
    with pytest.raises(GandalApiError) as caught:
        client.hypervisor.console("vm-9a6bd88b3c5f")
    assert (caught.value.status, caught.value.code) == (501, "not_implemented")


@respx.mock
def test_health_reports_pool_master(client: GandalClient) -> None:
    respx.get(f"{CELL}/health").respond(
        200, json={"status": "ok", "pool_master": "192.168.123.100", "version": "0.1.0"}
    )
    assert client.hypervisor.health().pool_master == "192.168.123.100"
