"""Transport HTTP partage (httpx) et mapping des erreurs API."""

from __future__ import annotations

from typing import Any

import httpx

from gandal_sdk.errors import GandalApiError


class HttpTransport:
    """Client HTTP synchrone avec Bearer et base URL."""

    def __init__(
        self,
        base_url: str,
        *,
        timeout: float = 30.0,
        client: httpx.Client | None = None,
    ) -> None:
        """Ouvre un client httpx pointe sur base_url, ou reutilise celui fourni."""
        self.base_url = base_url.rstrip("/")
        self._owns_client = client is None
        self._client = client or httpx.Client(base_url=self.base_url, timeout=timeout)
        self._token: str | None = None

    def set_token(self, token: str | None) -> None:
        """Enregistre le jeton Bearer utilise sur les appels suivants."""
        self._token = token

    @property
    def token(self) -> str | None:
        """Jeton Bearer courant, ou None si non authentifie."""
        return self._token

    def request(
        self,
        method: str,
        path: str,
        *,
        json: Any = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> Any:
        """Execute une requete et renvoie le JSON, ou None pour 204."""
        merged = dict(headers or {})
        if self._token:
            merged.setdefault("Authorization", f"Bearer {self._token}")
        response = self._client.request(
            method,
            path,
            json=json,
            params=params,
            headers=merged,
        )
        return self._parse(response)

    def close(self) -> None:
        """Ferme le client httpx s'il a ete cree par ce transport."""
        if self._owns_client:
            self._client.close()

    def _parse(self, response: httpx.Response) -> Any:
        """Traduit la reponse HTTP en donnee ou en GandalApiError."""
        if response.status_code == 204:
            return None
        content_type = response.headers.get("content-type", "")
        body: Any
        if "application/json" in content_type:
            body = response.json()
        else:
            body = response.text or None

        if response.is_success:
            return body

        code = "internal_error"
        message = response.reason_phrase or "Erreur HTTP"
        details: Any = None
        if isinstance(body, dict):
            err = body.get("error")
            if isinstance(err, dict):
                code = str(err.get("code") or code)
                message = str(err.get("message") or message)
                details = err.get("details")
            else:
                details = body
        raise GandalApiError(code, message, details=details, status=response.status_code)
