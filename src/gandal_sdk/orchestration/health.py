"""Sonde de sante de l'API d'orchestration."""

from __future__ import annotations

from gandal_sdk._http import HttpTransport
from gandal_sdk.orchestration.models import HealthOut


class HealthApi:
    """Sous-client health (/api/v1/health)."""

    def __init__(self, transport: HttpTransport) -> None:
        """Attache le transport HTTP partage."""
        self._http = transport

    def check(self) -> HealthOut:
        """Appelle GET /api/v1/health."""
        data = self._http.request("GET", "/api/v1/health")
        return HealthOut.model_validate(data)
