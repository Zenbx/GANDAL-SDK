"""Sonde de sante de l'API d'orchestration."""

from __future__ import annotations

from typing import Any

from gandal_sdk._http import HttpTransport


class HealthApi:
    """Sous-client health (/api/v1/health et /health)."""

    def __init__(self, transport: HttpTransport) -> None:
        """Attache le transport HTTP partage."""
        self._http = transport

    def check(self) -> Any:
        """Appelle GET /api/v1/health et renvoie le corps JSON."""
        return self._http.request("GET", "/api/v1/health")
