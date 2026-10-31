"""Facade orchestration : helpers typés + acces generique /api/v1."""

from __future__ import annotations

from typing import Any

from gandal_sdk._http import HttpTransport
from gandal_sdk.orchestration.auth import AuthApi
from gandal_sdk.orchestration.health import HealthApi
from gandal_sdk.orchestration.invitations import InvitationsApi
from gandal_sdk.orchestration.models import HealthOut
from gandal_sdk.orchestration.networks import NetworksApi
from gandal_sdk.orchestration.packs import PacksApi
from gandal_sdk.orchestration.profiles import ProfilesApi
from gandal_sdk.orchestration.projects import ProjectsApi
from gandal_sdk.orchestration.requests import RequestsApi
from gandal_sdk.orchestration.shares import SharesApi
from gandal_sdk.orchestration.storages import StoragesApi
from gandal_sdk.orchestration.vms import VmsApi


class OrchestrationApi:
    """Facade orchestration avec ressources typées."""

    def __init__(self, transport: HttpTransport) -> None:
        """Compose tous les sous-clients de l'API d'orchestration."""
        self._http = transport
        self.auth = AuthApi(transport)
        self._health = HealthApi(transport)
        self.projects = ProjectsApi(transport)
        self.invitations = InvitationsApi(transport)
        self.vms = VmsApi(transport)
        self.storages = StoragesApi(transport)
        self.networks = NetworksApi(transport)
        self.packs = PacksApi(transport)
        self.requests = RequestsApi(transport)
        self.shares = SharesApi(transport)
        self.profiles = ProfilesApi(transport)

    def health(self) -> HealthOut:
        """Retourne l'etat de sante de l'API d'orchestration."""
        return self._health.check()

    def get(self, path: str, *, params: dict[str, Any] | None = None) -> Any:
        """GET generique sous /api/v1 (echappatoire hors helpers typés)."""
        return self._http.request("GET", self._join(path), params=params)

    def post(self, path: str, *, json: Any = None) -> Any:
        """POST generique sous /api/v1."""
        return self._http.request("POST", self._join(path), json=json)

    def put(self, path: str, *, json: Any = None) -> Any:
        """PUT generique sous /api/v1."""
        return self._http.request("PUT", self._join(path), json=json)

    def patch(self, path: str, *, json: Any = None) -> Any:
        """PATCH generique sous /api/v1."""
        return self._http.request("PATCH", self._join(path), json=json)

    def delete(self, path: str, *, json: Any = None) -> Any:
        """DELETE generique sous /api/v1."""
        return self._http.request("DELETE", self._join(path), json=json)

    def _join(self, path: str) -> str:
        """Normalise un chemin relatif vers /api/v1/..."""
        if path.startswith("/api/v1"):
            return path
        if not path.startswith("/"):
            path = f"/{path}"
        return f"/api/v1{path}"
