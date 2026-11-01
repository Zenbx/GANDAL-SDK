"""Waiters des VMs contre une API simulee."""

import httpx
import pytest
import respx

from gandal_sdk import GandalClient
from gandal_sdk.orchestration.enums import VmState
from gandal_sdk.waiters import WaiterFailure, WaiterTimeout

VM_URL = "http://example.test/api/v1/projects/prj-1/vms/vm-1"
NOT_FOUND = {"error": {"code": "not_found", "message": "absente", "details": None}}


def _vm(state: str) -> httpx.Response:
    """Reponse GET de la VM dans l'etat donne."""
    return httpx.Response(
        200,
        json={
            "id": "vm-1",
            "origin_project_id": "prj-1",
            "name": "web-01",
            "ip_address": None,
            "ram_gb": 2,
            "vcpu": 1,
            "vram_gb": 0,
            "ssd_gb": 20,
            "state": state,
            "created_at": "2026-01-01T00:00:00Z",
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
def test_wait_until_running_goes_through_transitions(client) -> None:
    """pending -> creating -> unknown -> running : unknown n'est pas un succes."""
    respx.get(VM_URL).mock(
        side_effect=[_vm("pending"), _vm("creating"), _vm("unknown"), _vm("running")]
    )
    vm = client.orchestration.vms.wait_until_running("prj-1", "vm-1", delay=3.0)
    assert vm.state == VmState.RUNNING
    assert client.sleeps == [3.0, 3.0, 3.0]


@respx.mock
def test_wait_until_running_fails_fast_on_error(client) -> None:
    """Une VM en error ne demarrera pas : echec immediat avec la VM lue."""
    respx.get(VM_URL).mock(side_effect=[_vm("creating"), _vm("error")])
    with pytest.raises(WaiterFailure, match="etat error au lieu de running") as caught:
        client.orchestration.vms.wait_until_running("prj-1", "vm-1")
    assert caught.value.last_value.state == VmState.ERROR


@respx.mock
def test_wait_until_stopped_fails_if_vm_is_being_deleted(client) -> None:
    """Une VM en cours de suppression ne s'arretera pas : echec."""
    respx.get(VM_URL).mock(side_effect=[_vm("running"), _vm("deleting")])
    with pytest.raises(WaiterFailure, match="deleting"):
        client.orchestration.vms.wait_until_stopped("prj-1", "vm-1")


@respx.mock
def test_wait_until_stopped_times_out(client) -> None:
    """Toujours running apres max_attempts : WaiterTimeout."""
    route = respx.get(VM_URL).mock(return_value=_vm("running"))
    with pytest.raises(WaiterTimeout):
        client.orchestration.vms.wait_until_stopped("prj-1", "vm-1", max_attempts=4)
    assert route.call_count == 4


@respx.mock
def test_wait_until_deleted_ends_on_404(client) -> None:
    """deleting puis 404 : la suppression est terminee."""
    respx.get(VM_URL).mock(side_effect=[_vm("deleting"), httpx.Response(404, json=NOT_FOUND)])
    assert client.orchestration.vms.wait_until_deleted("prj-1", "vm-1") is None
    assert len(client.sleeps) == 1


@respx.mock
def test_wait_until_deleted_fails_on_error(client) -> None:
    """La suppression a echoue cote plateforme : la VM passe en error."""
    respx.get(VM_URL).mock(side_effect=[_vm("deleting"), _vm("error")])
    with pytest.raises(WaiterFailure, match="suppression a echoue"):
        client.orchestration.vms.wait_until_deleted("prj-1", "vm-1")
