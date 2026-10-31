"""Stub de la cellule Stockage (contrat aligne sur StoragePort)."""

from __future__ import annotations

from dataclasses import dataclass

from gandal_sdk.cells._base import not_ready


@dataclass(frozen=True)
class StorageSpec:
    """Nom et taille demandes au stockage."""

    name: str
    size_gb: int


@dataclass(frozen=True)
class StorageRef:
    """Reference d'un espace de stockage."""

    storage_id: str
    ip_address: str | None = None


class StorageCell:
    """Client de la cellule Stockage. Stub jusqu'a publication de son API."""

    def create_storage(self, spec: StorageSpec) -> StorageRef:
        """Cree un espace (pas encore disponible)."""
        not_ready("storage")

    def resize(self, ref: StorageRef, size_gb: int) -> None:
        """Redimensionne un espace (pas encore disponible)."""
        not_ready("storage")

    def delete_storage(self, ref: StorageRef) -> None:
        """Supprime un espace (pas encore disponible)."""
        not_ready("storage")
