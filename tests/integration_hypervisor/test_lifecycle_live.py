"""Cycle de vie complet d'une VM, du SDK jusqu'au pool, via la cellule."""

import pytest

from gandal_sdk import GandalApiError
from gandal_sdk.cells.hypervisor import HypervisorCell, OperationStatus, PowerAction, VmSpec
from gandal_sdk.orchestration.enums import VmState

from .conftest import PREFIX, WAIT


def _spec(default_name: str, **overrides) -> VmSpec:
    values = {"name": default_name, "ram_gb": 1, "vcpu": 1, "vram_gb": 0, "ssd_gb": 10}
    return VmSpec(**{**values, **overrides})


def test_cell_reaches_pool_master(cell: HypervisorCell) -> None:
    health = cell.health()
    assert health.status == "ok" and health.pool_master


def test_only_managed_vms_are_listed(cell: HypervisorCell) -> None:
    """Les VM de production du pool n'apparaissent jamais."""
    assert all(vm.name.startswith(PREFIX) for vm in cell.list_vms())


def test_full_lifecycle(cell: HypervisorCell, vm_name: str) -> None:
    created = cell.create_vm(_spec(vm_name))
    assert created.vm.state == VmState.CREATING
    assert cell.wait_for_operation(created.operation, **WAIT).status == OperationStatus.SUCCEEDED

    running = cell.wait_until_running(created.vm, **WAIT)
    assert (running.name, running.vcpu, running.ram_gb) == (vm_name, 1, 1)
    assert running.host and running.xapi_uuid

    cell.wait_for_operation(cell.power(running, PowerAction.STOP), **WAIT)
    stopped = cell.wait_until_stopped(running, **WAIT)

    grown = cell.wait_for_operation(
        cell.update_vm(stopped, _spec(vm_name, ssd_gb=stopped.ssd_gb + 1)), **WAIT
    )
    assert grown.status == OperationStatus.SUCCEEDED
    assert cell.get_vm(stopped).ssd_gb == stopped.ssd_gb + 1

    cell.wait_for_operation(cell.power(stopped, PowerAction.START), **WAIT)
    cell.wait_until_running(stopped, **WAIT)
    cell.wait_for_operation(cell.power(stopped, PowerAction.RESTART), **WAIT)
    cell.wait_until_running(stopped, **WAIT)

    cell.wait_for_operation(cell.delete_vm(stopped), **WAIT)
    cell.wait_until_deleted(stopped, **WAIT)
    with pytest.raises(GandalApiError) as caught:
        cell.get_vm(stopped)
    assert caught.value.code == "not_found"


@pytest.mark.parametrize(
    ("overrides", "field"),
    [({"name": "prod-web"}, "name"), ({"vcpu": 2}, "vcpu"), ({"ram_gb": 2}, "ram_gb")],
)
def test_sandbox_refuses_out_of_scope_requests(
    cell: HypervisorCell, vm_name: str, overrides: dict, field: str
) -> None:
    """Refus immediat (403), avant tout appel au pool."""
    with pytest.raises(GandalApiError) as caught:
        cell.create_vm(_spec(vm_name, **overrides))
    assert (caught.value.status, caught.value.details["field"]) == (403, field)


def test_disk_cannot_shrink(cell: HypervisorCell, vm_name: str) -> None:
    """Un disque plus petit que le modele : l'operation echoue proprement, rien ne reste."""
    created = cell.create_vm(_spec(vm_name, ssd_gb=1))
    with pytest.raises(Exception) as caught:
        cell.wait_for_operation(created.operation, **WAIT)
    assert "validation_error" in str(caught.value)
    assert cell.get_vm(created.vm).state == VmState.ERROR
    cell.delete_vm(created.vm)
    with pytest.raises(GandalApiError):
        cell.get_vm(created.vm)
