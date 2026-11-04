"""Cas limites des stubs cellules : chaque methode publique leve CellUnavailable."""

import pytest

from gandal_sdk.cells.dns import DnsCell
from gandal_sdk.cells.hypervisor import HypervisorCell, PowerAction, VmRef, VmSpec
from gandal_sdk.cells.iam import IamCell
from gandal_sdk.cells.network import NetworkCell, NetworkRef
from gandal_sdk.cells.notifications import Notification, NotificationsCell
from gandal_sdk.cells.storage import StorageCell, StorageRef, StorageSpec
from gandal_sdk.errors import CellUnavailable


def test_iam_unconfigured_raises() -> None:
    """Sans endpoint IAM, les operations levent CellUnavailable."""
    cell = IamCell()
    with pytest.raises(CellUnavailable):
        cell.decide({"action": "vm:create", "ressource": {"type": "vm"}})
    with pytest.raises(CellUnavailable):
        cell.list_subjects()
    with pytest.raises(CellUnavailable):
        cell.get_me()


def test_hypervisor_methods_raise() -> None:
    """Toutes les operations hyperviseur stubbees echouent clairement."""
    cell = HypervisorCell()
    ref = VmRef(vm_id="vm-1")
    spec = VmSpec(name="v", ram_gb=2, vcpu=2, vram_gb=0, ssd_gb=20)
    with pytest.raises(CellUnavailable):
        cell.update_vm(ref, spec)
    with pytest.raises(CellUnavailable):
        cell.power(ref, PowerAction.START)
    with pytest.raises(CellUnavailable):
        cell.console(ref)
    with pytest.raises(CellUnavailable):
        cell.delete_vm(ref)


def test_network_methods_raise() -> None:
    """Toutes les operations reseau stubbees echouent clairement."""
    cell = NetworkCell()
    net = NetworkRef(network_id="n1")
    vm = VmRef(vm_id="vm-1")
    with pytest.raises(CellUnavailable):
        cell.rename_network(net, "x")
    with pytest.raises(CellUnavailable):
        cell.attach_vm(net, vm)
    with pytest.raises(CellUnavailable):
        cell.detach_vm(net, vm)
    with pytest.raises(CellUnavailable):
        cell.detach_vm_from_project(vm, "p")
    with pytest.raises(CellUnavailable):
        cell.delete_network(net)


def test_storage_methods_raise() -> None:
    """Toutes les operations stockage stubbees echouent clairement."""
    cell = StorageCell()
    ref = StorageRef(storage_id="s1")
    with pytest.raises(CellUnavailable):
        cell.resize(ref, 50)
    with pytest.raises(CellUnavailable):
        cell.delete_storage(ref)
    with pytest.raises(CellUnavailable):
        cell.create_storage(StorageSpec(name="s", size_gb=1))


def test_dns_and_notifications_raise() -> None:
    """DNS et notifications stubbes echouent clairement."""
    with pytest.raises(CellUnavailable):
        DnsCell().delete_domain("vm")
    with pytest.raises(CellUnavailable):
        NotificationsCell().notify(Notification(user_id="u", subject="s", message="m"))
