"""Helpers typés pour les invitations recues (/api/v1/invitations)."""

from __future__ import annotations

from gandal_sdk._http import HttpTransport
from gandal_sdk.orchestration._util import drop_none, parse_page
from gandal_sdk.orchestration.enums import InvitationStatus
from gandal_sdk.orchestration.models import InvitationOut, Page


class InvitationsApi:
    """Sous-client typé des invitations de l'appelant."""

    def __init__(self, transport: HttpTransport) -> None:
        """Attache le transport HTTP partage."""
        self._http = transport

    def list(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        status: InvitationStatus | str | None = None,
    ) -> Page[InvitationOut]:
        """Liste les invitations recues."""
        data = self._http.request(
            "GET",
            "/api/v1/invitations",
            params=drop_none(
                {"page": page, "page_size": page_size, "status": status}
            ),
        )
        return parse_page(data, InvitationOut)

    def accept(self, invitation_id: str) -> InvitationOut:
        """Accepte une invitation."""
        data = self._http.request(
            "POST",
            f"/api/v1/invitations/{invitation_id}/accept",
        )
        return InvitationOut.model_validate(data)

    def refuse(self, invitation_id: str) -> InvitationOut:
        """Refuse une invitation."""
        data = self._http.request(
            "POST",
            f"/api/v1/invitations/{invitation_id}/refuse",
        )
        return InvitationOut.model_validate(data)

    def cancel(self, invitation_id: str) -> InvitationOut:
        """Annule une invitation emise."""
        data = self._http.request(
            "POST",
            f"/api/v1/invitations/{invitation_id}/cancel",
        )
        return InvitationOut.model_validate(data)
