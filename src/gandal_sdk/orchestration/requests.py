"""Helpers typés pour le moteur de demandes."""

from __future__ import annotations

from typing import cast

from gandal_sdk._http import HttpTransport
from gandal_sdk.orchestration._util import drop_none, parse_page
from gandal_sdk.orchestration.enums import RequestKind, RequestStatus
from gandal_sdk.orchestration.models import Page, RequestDecisionIn, RequestOut
from gandal_sdk.waiters import wait_for

# Une decision humaine se compte en minutes : interroger moins souvent, plus longtemps.
DECISION_DELAY = 15.0
DECISION_MAX_ATTEMPTS = 240  # 1 heure


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

    def wait_until_accepted(
        self,
        request_id: str,
        *,
        delay: float = DECISION_DELAY,
        max_attempts: int = DECISION_MAX_ATTEMPTS,
    ) -> RequestOut:
        """Attend l'acceptation d'une demande par un administrateur.

        Leve WaiterFailure si elle est refusee ou annulee. Pour une creation,
        target_resource_id de la demande renvoyee designe la ressource creee.
        """
        request = wait_for(
            lambda: self.get(request_id),
            is_success=lambda req: req.status == RequestStatus.ACCEPTED,
            failure_reason=_refusal_reason,
            description=f"Demande {request_id}",
            delay=delay,
            max_attempts=max_attempts,
            sleep=self._http.sleep,
        )
        # gone_is_success desactive : wait_for ne renvoie jamais GONE ici.
        return cast(RequestOut, request)


def _refusal_reason(request: RequestOut) -> str | None:
    """Message d'echec pour une demande refusee ou annulee, None sinon."""
    if request.status not in (RequestStatus.REFUSED, RequestStatus.CANCELLED):
        return None
    note = f" ({request.admin_note})" if request.admin_note else ""
    return f"{request.status}{note}"
