"""Facade unique du SDK GANDAL pour les apps externes."""

from __future__ import annotations

from gandal_sdk._http import HttpTransport
from gandal_sdk.cells.dns import DnsCell
from gandal_sdk.cells.hypervisor import HypervisorCell
from gandal_sdk.cells.iam import IamCell
from gandal_sdk.cells.network import NetworkCell
from gandal_sdk.cells.notifications import NotificationsCell
from gandal_sdk.cells.storage import StorageCell
from gandal_sdk.orchestration.api import OrchestrationApi
from gandal_sdk.orchestration.auth import IdentityOut, TokenOut


class GandalClient:
    """Point d'entree unique : orchestration + cellules (stubs inclus)."""

    def __init__(
        self,
        base_url: str,
        *,
        timeout: float = 30.0,
        cell_urls: dict[str, str] | None = None,
    ) -> None:
        """Initialise le transport d'orchestration et les sous-clients cellules.

        cell_urls est reserve pour brancher plus tard des hosts distincts par cellule.
        """
        self._cell_urls = dict(cell_urls or {})
        self._http = HttpTransport(base_url, timeout=timeout)
        self.orchestration = OrchestrationApi(self._http)
        self.iam = IamCell()
        self.hypervisor = HypervisorCell()
        self.network = NetworkCell()
        self.storage = StorageCell()
        self.dns = DnsCell()
        self.notifications = NotificationsCell()

    def login(self, email: str, password: str) -> TokenOut:
        """Authentifie via l'orchestration et conserve le Bearer pour les appels suivants."""
        token = self.orchestration.auth.login(email, password)
        self._http.set_token(token.access_token)
        return token

    def me(self) -> IdentityOut:
        """Raccourci vers l'identite courante (orchestration)."""
        return self.orchestration.auth.me()

    def set_token(self, token: str) -> None:
        """Injecte un jeton Bearer deja obtenu ailleurs."""
        self._http.set_token(token)

    def close(self) -> None:
        """Ferme les connexions HTTP du client."""
        self._http.close()

    def __enter__(self) -> GandalClient:
        """Permet l'usage en context manager."""
        return self

    def __exit__(self, *args: object) -> None:
        """Ferme le client a la sortie du context manager."""
        self.close()
