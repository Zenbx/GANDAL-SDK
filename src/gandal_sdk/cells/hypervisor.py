"""Stub de la cellule Hyperviseur (contrat aligne sur HypervisorPort)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from gandal_sdk.cells._base import not_ready


class PowerAction(StrEnum):
    """Action d'alimentation d'une VM."""

    START = "start"
    STOP = "stop"
    RESTART = "restart"


@dataclass(frozen=True)
class VmSpec:
    """Caracteristiques demandees a l'hyperviseur."""

    name: str
    ram_gb: int
    vcpu: int
    vram_gb: int
    ssd_gb: int


@dataclass(frozen=True)
class VmRef:
    """Reference d'une VM cote hyperviseur."""

    vm_id: str
    ip_address: str | None = None


@dataclass(frozen=True)
class ConsoleAccess:
    """Acces console graphique temporaire."""

    url: str
    expires_in: int


class HypervisorCell:
    """Client de la cellule Hyperviseur. Stub jusqu'a publication de son API."""

    def create_vm(self, spec: VmSpec) -> VmRef:
        """Cree une VM (pas encore disponible)."""
        not_ready("hypervisor")

    def update_vm(self, ref: VmRef, spec: VmSpec) -> None:
        """Met a jour une VM (pas encore disponible)."""
        not_ready("hypervisor")

    def power(self, ref: VmRef, action: PowerAction) -> None:
        """Change l'alimentation d'une VM (pas encore disponible)."""
        not_ready("hypervisor")

    def console(self, ref: VmRef) -> ConsoleAccess:
        """Ouvre un acces console (pas encore disponible)."""
        not_ready("hypervisor")

    def delete_vm(self, ref: VmRef) -> None:
        """Supprime une VM (pas encore disponible)."""
        not_ready("hypervisor")
