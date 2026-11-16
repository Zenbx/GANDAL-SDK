"""Helpers typés pour profils et catalogue de droits."""

from __future__ import annotations

from gandal_sdk._http import HttpTransport
from gandal_sdk.orchestration._util import parse_page
from gandal_sdk.orchestration.auth import IdentityOut
from gandal_sdk.orchestration.models import (
    Page,
    ProfileCreateIn,
    ProfileOut,
    ProfileUpdateIn,
    RegisterIn,
    RightOut,
)


class ProfilesApi:
    """Sous-client typé /api/v1/admin/rights et /profiles."""

    def __init__(self, transport: HttpTransport) -> None:
        """Attache le transport HTTP partage."""
        self._http = transport

    def list_rights(self) -> list[RightOut]:
        """Liste le catalogue de droits."""
        data = self._http.request("GET", "/api/v1/admin/rights")
        return [RightOut.model_validate(item) for item in data]

    def list(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> Page[ProfileOut]:
        """Liste les profils de droits."""
        data = self._http.request(
            "GET",
            "/api/v1/admin/profiles",
            params={"page": page, "page_size": page_size},
        )
        return parse_page(data, ProfileOut)

    def create(self, body: ProfileCreateIn) -> ProfileOut:
        """Cree un profil (administrateur)."""
        data = self._http.request(
            "POST",
            "/api/v1/admin/profiles",
            json=body.model_dump(),
        )
        return ProfileOut.model_validate(data)

    def update(self, profile_id: str, body: ProfileUpdateIn) -> ProfileOut:
        """Modifie un profil (administrateur)."""
        data = self._http.request(
            "PATCH",
            f"/api/v1/admin/profiles/{profile_id}",
            json=body.model_dump(exclude_unset=True),
        )
        return ProfileOut.model_validate(data)

    def delete(self, profile_id: str) -> None:
        """Supprime un profil (administrateur)."""
        self._http.request("DELETE", f"/api/v1/admin/profiles/{profile_id}")


    def create_admin(self, body: RegisterIn) -> IdentityOut:
        """Cree un administrateur (POST /api/v1/admin/admins).

        Rend l'IDENTITE creee, pas un jeton : contrairement a `auth.register`,
        celui qui cree l'administrateur n'est pas celui qui l'utilisera. Rendre
        un jeton ici reviendrait a connecter l'appelant sous l'identite qu'il
        vient de creer pour quelqu'un d'autre.
        """
        data = self._http.request(
            "POST", "/api/v1/admin/admins", json=body.model_dump())
        return IdentityOut.model_validate(data)
