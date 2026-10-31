"""Helpers typés pour le moteur de demandes."""

from __future__ import annotations

from gandal_sdk._http import HttpTransport
from gandal_sdk.orchestration._util import drop_none, parse_page
from gandal_sdk.orchestration.enums import RequestKind, RequestStatus
from gandal_sdk.orchestration.models import Page, RequestDecisionIn, RequestOut


class RequestsApi:
    """Sous-client typé /api/v1/requests."""

    def __init__(self, transport: HttpTransport) -> None:
        """Attache le transport HTTP partage."""
        self._http = transport

    def list(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        status: RequestStatus | str | None = None,
        kind: RequestKind | str | None = None,
        project_id: str | None = None,
        author_id: str | None = None,
    ) -> Page[RequestOut]:
        """Liste les demandes visibles."""
        data = self._http.request(
            "GET",
            "/api/v1/requests",
            params=drop_none(
                {
                    "page": page,
                    "page_size": page_size,
                    "status": status,
                    "kind": kind,
                    "project_id": project_id,
                    "author_id": author_id,
                }
            ),
        )
        return parse_page(data, RequestOut)

    def get(self, request_id: str) -> RequestOut:
        """Consulte une demande."""
        data = self._http.request("GET", f"/api/v1/requests/{request_id}")
        return RequestOut.model_validate(data)

    def cancel(self, request_id: str) -> RequestOut:
        """Annule une demande en attente (auteur)."""
        data = self._http.request(
            "POST",
            f"/api/v1/requests/{request_id}/cancel",
        )
        return RequestOut.model_validate(data)

    def accept(
        self,
        request_id: str,
        *,
        note: str | None = None,
    ) -> RequestOut:
        """Accepte une demande (administrateur)."""
        body = RequestDecisionIn(note=note)
        data = self._http.request(
            "POST",
            f"/api/v1/requests/{request_id}/accept",
            json=body.model_dump(),
        )
        return RequestOut.model_validate(data)

    def refuse(
        self,
        request_id: str,
        *,
        note: str | None = None,
    ) -> RequestOut:
        """Refuse une demande (administrateur)."""
        body = RequestDecisionIn(note=note)
        data = self._http.request(
            "POST",
            f"/api/v1/requests/{request_id}/refuse",
            json=body.model_dump(),
        )
        return RequestOut.model_validate(data)
