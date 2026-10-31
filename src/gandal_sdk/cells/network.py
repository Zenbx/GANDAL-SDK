"""Stub de la cellule Reseau (contrat aligne sur NetworkPort)."""

from __future__ import annotations

from dataclasses import dataclass

from gandal_sdk.cells._base import not_ready
from gandal_sdk.cells.hypervisor import VmRef


@dataclass(frozen=True)
class NetworkRef:
    """Reference d'un reseau cote cellule Reseau."""

    network_id: str


class NetworkCell:
    """Client de la cellule Reseau. Stub jusqu'a publication de son API."""

    def create_network(self, project_id: str, name: str) -> NetworkRef:
        """Cree un reseau (pas encore disponible)."""
        not_ready("network")

    def rename_network(self, network: NetworkRef, name: str) -> None:
        """Renomme un reseau (pas encore disponible)."""
        not_ready("network")

    def attach_vm(self, network: NetworkRef, vm: VmRef) -> None:
        """Rattache une VM a un reseau (pas encore disponible)."""
        not_ready("network")

    def detach_vm(self, network: NetworkRef, vm: VmRef) -> None:
        """Detache une VM d'un reseau (pas encore disponible)."""
        not_ready("network")

    def detach_vm_from_project(self, vm: VmRef, project_id: str) -> None:
        """Retire une VM de tous les reseaux d'un projet (pas encore disponible)."""
        not_ready("network")

    def delete_network(self, network: NetworkRef) -> None:
        """Supprime un reseau (pas encore disponible)."""
        not_ready("network")
