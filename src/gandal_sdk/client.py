"""Facade unique du SDK GANDAL pour les apps externes."""

from __future__ import annotations

from gandal_sdk._http import HttpTransport, RetryPolicy
from gandal_sdk.cells.dns import DnsCell
from gandal_sdk.cells.hypervisor import HypervisorCell
from gandal_sdk.cells.iam import IamCell
from gandal_sdk.cells.network import NetworkCell
from gandal_sdk.cells.notifications import NotificationsCell
from gandal_sdk.cells.storage import StorageCell
from gandal_sdk.credentials import resolve_credentials
from gandal_sdk.orchestration.api import OrchestrationApi
from gandal_sdk.orchestration.auth import IdentityOut, TokenOut


class GandalClient:
    """Point d'entree unique : orchestration + cellules (stubs inclus)."""

    def __init__(
        self,
        base_url: str,
        *,
        timeout: float = 30.0,
        retry: RetryPolicy | None = None,
        cell_urls: dict[str, str] | None = None,
        cell_tokens: dict[str, str] | None = None,
    ) -> None:
        """Initialise le transport d'orchestration et les sous-clients cellules.

        retry regle les relances automatiques ; RetryPolicy(max_attempts=1) les desactive.
        cell_urls / cell_tokens : endpoint et jeton propres a chaque cellule, par nom
        (aujourd'hui « hypervisor ») ; une cellule sans endpoint leve CellUnavailable.
        """
        self._cell_urls = dict(cell_urls or {})
        self._cell_transports: list[HttpTransport] = []
        self._http = HttpTransport(base_url, timeout=timeout, retry=retry)
        self.orchestration = OrchestrationApi(self._http)
        self.iam = IamCell()
        self.hypervisor = HypervisorCell(
            self._cell_transport("hypervisor", timeout, retry, cell_tokens or {})
        )
        self.network = NetworkCell()
        self.storage = StorageCell()
        self.dns = DnsCell()
        self.notifications = NotificationsCell()

    @classmethod
    def from_env(
        cls,
        *,
        endpoint: str | None = None,
        token: str | None = None,
        profile: str | None = None,
        timeout: float = 30.0,
        retry: RetryPolicy | None = None,
    ) -> GandalClient:
        """Construit un client a partir de la chaine d'identifiants (gandal_sdk.credentials).

        Les arguments explicites l'emportent sur GANDAL_ENDPOINT / GANDAL_TOKEN,
        qui l'emportent sur le profil de ~/.gandal/credentials.
        """
        credentials = resolve_credentials(endpoint=endpoint, token=token, profile=profile)
        cell_urls, cell_tokens = {}, {}
        if credentials.hypervisor_endpoint:
            cell_urls["hypervisor"] = credentials.hypervisor_endpoint
            if credentials.hypervisor_token:
                cell_tokens["hypervisor"] = credentials.hypervisor_token
        client = cls(
            credentials.endpoint,
            timeout=timeout,
            retry=retry,
            cell_urls=cell_urls,
            cell_tokens=cell_tokens,
        )
        if credentials.token:
            client.set_token(credentials.token)
        return client

    def _cell_transport(
        self, name: str, timeout: float, retry: RetryPolicy | None, tokens: dict[str, str]
    ) -> HttpTransport | None:
        url = self._cell_urls.get(name)
        if not url:
            return None
        transport = HttpTransport(url, timeout=timeout, retry=retry)
        transport.set_token(tokens.get(name))
        self._cell_transports.append(transport)
        return transport

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
        """Ferme les connexions HTTP du client et de ses cellules."""
        self._http.close()
        for transport in self._cell_transports:
            transport.close()

    def __enter__(self) -> GandalClient:
        """Permet l'usage en context manager."""
        return self

    def __exit__(self, *args: object) -> None:
        """Ferme le client a la sortie du context manager."""
        self.close()
