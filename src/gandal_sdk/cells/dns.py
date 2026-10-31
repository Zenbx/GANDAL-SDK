"""Stub de la cellule DNS (contrat aligne sur DnsPort)."""

from __future__ import annotations

from gandal_sdk.cells._base import not_ready


class DnsCell:
    """Client de la cellule DNS. Stub jusqu'a publication de son API."""

    def delete_domain(self, vm_id: str) -> None:
        """Supprime le nom de domaine d'une VM (pas encore disponible)."""
        not_ready("dns")
