"""Acces generique aux routes /api/v1 de l'orchestration."""

from __future__ import annotations

from typing import Any

from gandal_sdk._http import HttpTransport
from gandal_sdk.orchestration.auth import AuthApi
from gandal_sdk.orchestration.health import HealthApi


class OrchestrationApi:
    """Facade orchestration : auth, health, et requetes generiques."""

    def __init__(self, transport: HttpTransport) -> None:
        """Compose les sous-clients auth et health."""
        self._http = transport
        self.auth = AuthApi(transport)
        self._health = HealthApi(transport)

    def health(self) -> Any:
        """Retourne l'etat de sante de l'API d'orchestration."""
        return self._health.check()

    def get(self, path: str, *, params: dict[str, Any] | None = None) -> Any:
        """GET sous /api/v1 (path relatif, ex. /projects)."""
        return self._http.request("GET", self._join(path), params=params)

    def post(self, path: str, *, json: Any = None) -> Any:
        """POST sous /api/v1."""
        return self._http.request("POST", self._join(path), json=json)

    def put(self, path: str, *, json: Any = None) -> Any:
        """PUT sous /api/v1."""
        return self._http.request("PUT", self._join(path), json=json)

    def patch(self, path: str, *, json: Any = None) -> Any:
        """PATCH sous /api/v1."""
        return self._http.request("PATCH", self._join(path), json=json)

    def delete(self, path: str, *, json: Any = None) -> Any:
        """DELETE sous /api/v1."""
        return self._http.request("DELETE", self._join(path), json=json)

    def _join(self, path: str) -> str:
        """Normalise un chemin relatif vers /api/v1/..."""
        if path.startswith("/api/v1"):
            return path
        if not path.startswith("/"):
            path = f"/{path}"
        return f"/api/v1{path}"
