"""Utilitaire commun aux stubs de cellules."""

from __future__ import annotations

from gandal_sdk.errors import CellUnavailable


def not_ready(cell_name: str) -> None:
    """Leve CellUnavailable pour une cellule pas encore branchee."""
    raise CellUnavailable(cell_name)
