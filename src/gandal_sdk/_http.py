"""Transport HTTP partage (httpx) et mapping des erreurs API."""

from __future__ import annotations

import random
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import httpx

from gandal_sdk.errors import GandalApiError

# Code metier par statut HTTP (API_ENDPOINTS.md §1.4), quand la reponse n'a pas
# l'enveloppe {error: {...}} : erreurs par defaut de FastAPI ({"detail": ...}),
# proxy, ou route inexistante.
_CODE_BY_STATUS = {
    400: "bad_request",
    401: "unauthorized",
    403: "forbidden",
    404: "not_found",
    409: "conflict",
    422: "validation_error",
    429: "throttled",
    503: "upstream_unavailable",
}

# Methodes qu'on peut rejouer sans risque de doublon (docs/CONVENTIONS_API.md §5).
_IDEMPOTENT_METHODS = frozenset({"GET", "HEAD", "OPTIONS", "PUT", "DELETE"})


@dataclass(frozen=True)
class RetryPolicy:
    """Relances automatiques : nombre de tentatives et bornes de l'attente."""

    max_attempts: int = 3
    base_delay: float = 0.5
    max_delay: float = 20.0

    def delay(self, attempt: int, retry_after: str | None) -> float:
        """Attente avant la tentative suivante : Retry-After, sinon exponentielle avec gigue."""
        if retry_after is not None:
            try:
                return min(self.max_delay, max(0.0, float(retry_after)))
            except ValueError:
                pass  # date HTTP : on retombe sur l'attente exponentielle
        ceiling = min(self.max_delay, self.base_delay * 2 ** (attempt - 1))
        return random.uniform(ceiling / 2, ceiling)


class HttpTransport:
    """Client HTTP synchrone avec Bearer et base URL."""

    def __init__(
        self,
        base_url: str,
        *,
        timeout: float = 30.0,
        client: httpx.Client | None = None,
        retry: RetryPolicy | None = None,
        sleep: Callable[[float], None] = time.sleep,
        verify: bool | str = True,
    ) -> None:
        """Ouvre un client httpx pointe sur base_url, ou reutilise celui fourni.

        verify : True (CA systeme), False (TLS non verifie), ou chemin vers un
        fichier de certificats (ex. gandal-ca.crt pour la cellule IAM).
        """
        self.base_url = base_url.rstrip("/")
        self.retry = retry or RetryPolicy()
        self.sleep = sleep
        self._owns_client = client is None
        self._client = client or httpx.Client(
            base_url=self.base_url, timeout=timeout, verify=verify
        )
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
        """Execute une requete et renvoie le JSON, ou None pour 204.

        Relance selon self.retry les 429, et pour une requete rejouable
        (methode idempotente ou en-tete Idempotency-Key) les 503 et erreurs reseau.
        """
        merged = dict(headers or {})
        if self._token:
            merged.setdefault("Authorization", f"Bearer {self._token}")
        replayable = method.upper() in _IDEMPOTENT_METHODS or any(
            name.lower() == "idempotency-key" for name in merged
        )
        attempt = 1
        while True:
            try:
                response = self._client.request(
                    method,
                    path,
                    json=json,
                    params=params,
                    headers=merged,
                )
            except httpx.TransportError:
                if not replayable or attempt >= self.retry.max_attempts:
                    raise
                self.sleep(self.retry.delay(attempt, None))
                attempt += 1
                continue
            retryable = response.status_code == 429 or (
                response.status_code == 503 and replayable
            )
            if not retryable or attempt >= self.retry.max_attempts:
                return self._parse(response)
            self.sleep(self.retry.delay(attempt, response.headers.get("retry-after")))
            attempt += 1

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
        # application/json et application/problem+json (RFC 9457, cellule IAM).
        if "json" in content_type:
            body = response.json()
        else:
            body = response.text or None

        if response.is_success:
            return body

        code = _CODE_BY_STATUS.get(response.status_code, "internal_error")
        message = response.reason_phrase or "Erreur HTTP"
        details: Any = None
        if isinstance(body, dict):
            err = body.get("error")
            detail = body.get("detail")
            if isinstance(err, dict):
                code = str(err.get("code") or code)
                message = str(err.get("message") or message)
                details = err.get("details")
            elif "type" in body and "title" in body:
                # RFC 9457 : type URI + title + detail + correlation_id.
                type_uri = str(body.get("type") or "")
                code = type_uri.rstrip("/").rsplit("/", 1)[-1] or str(body["title"])
                message = str(detail) if isinstance(detail, str) else str(body["title"])
                details = {
                    k: body[k]
                    for k in ("type", "title", "status", "correlation_id")
                    if k in body
                }
            elif isinstance(detail, str):
                message = detail
            elif detail is not None:
                details = detail  # liste d'erreurs de validation de FastAPI
            else:
                details = body
        raise GandalApiError(code, message, details=details, status=response.status_code)
