"""Exceptions publiques du SDK GANDAL."""

from __future__ import annotations

from typing import Any


class GandalError(Exception):
    """Erreur de base du SDK."""


class GandalApiError(GandalError):
    """Erreur renvoyee par un service GANDAL au format {error: {code, message, details}}."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        details: Any = None,
        status: int | None = None,
    ) -> None:
        """Conserve le code metier et le statut HTTP pour l'appelant."""
        super().__init__(f"[{code}] {message}")
        self.code = code
        self.message = message
        self.details = details
        self.status = status


class CellUnavailable(GandalError):
    """La cellule visee n'est pas encore branchee dans le SDK."""

    def __init__(self, cell_name: str) -> None:
        """Indique quelle cellule manque encore."""
        super().__init__(
            f"La cellule '{cell_name}' n'est pas encore disponible dans le SDK GANDAL."
        )
        self.cell_name = cell_name
