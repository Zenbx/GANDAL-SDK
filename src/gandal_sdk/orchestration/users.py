"""Helpers typés pour l'annuaire admin des comptes (/api/v1/admin/users)."""

from __future__ import annotations

from gandal_sdk._http import HttpTransport
from gandal_sdk.orchestration._util import parse_page
from gandal_sdk.orchestration.auth import IdentityOut
from gandal_sdk.orchestration.models import Page, UserOverviewOut


class UsersApi:
    """Sous-client typé /api/v1/admin/users (administrateur)."""

    def __init__(self, transport: HttpTransport) -> None:
        """Attache le transport HTTP partage."""
        self._http = transport

    def list(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> Page[IdentityOut]:
        """Liste les identites IAM connues (administrateurs inclus)."""
        data = self._http.request(
            "GET",
            "/api/v1/admin/users",
            params={"page": page, "page_size": page_size},
        )
        return parse_page(data, IdentityOut)

    def overview(self, user_id: str) -> UserOverviewOut:
        """Vue operationnelle d'un compte (projets, invitations, demandes, partages)."""
        data = self._http.request(
            "GET",
            f"/api/v1/admin/users/{user_id}/overview",
        )
        return UserOverviewOut.model_validate(data)
