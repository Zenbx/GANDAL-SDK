"""Sonde de sante de l'API d'orchestration."""

from __future__ import annotations

from gandal_sdk._http import HttpTransport
from gandal_sdk.orchestration.models import HealthOut, ReadinessOut


class HealthApi:
    """Sous-client health (/api/v1/health)."""

    def __init__(self, transport: HttpTransport) -> None:
        """Attache le transport HTTP partage."""
        self._http = transport

    def check(self) -> HealthOut:
        """Appelle GET /api/v1/health : le processus repond-il ?"""
        data = self._http.request("GET", "/api/v1/health")
        return HealthOut.model_validate(data)

    def ready(self) -> ReadinessOut:
        """Appelle GET /ready : l'API peut-elle SERVIR ?

        `check` dit que le processus repond ; `ready` qu'il a ses dependances.
        C'est `ready` que vise une sonde d'orchestrateur avant d'envoyer du
        trafic — et noter que la route n'est PAS sous `/api/v1`.
        """
        data = self._http.request("GET", "/ready")
        return ReadinessOut.model_validate(data)
