"""Helpers typés pour le catalogue de packs."""

from __future__ import annotations

from gandal_sdk._http import HttpTransport
from gandal_sdk.orchestration._util import drop_none, parse_page
from gandal_sdk.orchestration.models import PackCreateIn, PackOut, PackUpdateIn, Page


class PacksApi:
    """Sous-client typé /api/v1/packs et /api/v1/admin/packs."""

    def __init__(self, transport: HttpTransport) -> None:
        """Attache le transport HTTP partage."""
        self._http = transport

    def list(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        name: str | None = None,
        min_ram_gb: int | None = None,
        max_ram_gb: int | None = None,
        min_vcpu: int | None = None,
        max_vcpu: int | None = None,
    ) -> Page[PackOut]:
        """Liste le catalogue de packs."""
        data = self._http.request(
            "GET",
            "/api/v1/packs",
            params=drop_none(
                {
                    "page": page,
                    "page_size": page_size,
                    "name": name,
                    "min_ram_gb": min_ram_gb,
                    "max_ram_gb": max_ram_gb,
                    "min_vcpu": min_vcpu,
                    "max_vcpu": max_vcpu,
                }
            ),
        )
        return parse_page(data, PackOut)

    def get(self, pack_id: str) -> PackOut:
        """Lit un pack."""
        data = self._http.request("GET", f"/api/v1/packs/{pack_id}")
        return PackOut.model_validate(data)

    def create(self, body: PackCreateIn) -> PackOut:
        """Cree un pack (administrateur)."""
        data = self._http.request(
            "POST",
            "/api/v1/admin/packs",
            json=body.model_dump(),
        )
        return PackOut.model_validate(data)

    def update(self, pack_id: str, body: PackUpdateIn) -> PackOut:
        """Modifie un pack (administrateur)."""
        data = self._http.request(
            "PATCH",
            f"/api/v1/admin/packs/{pack_id}",
            json=body.model_dump(exclude_none=True),
        )
        return PackOut.model_validate(data)

    def delete(self, pack_id: str) -> None:
        """Supprime un pack (administrateur)."""
        self._http.request("DELETE", f"/api/v1/admin/packs/{pack_id}")
