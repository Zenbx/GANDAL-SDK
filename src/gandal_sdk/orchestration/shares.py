"""Helpers typés pour les partages."""

from __future__ import annotations

from gandal_sdk._http import HttpTransport
from gandal_sdk.orchestration._util import drop_none, parse_page
from gandal_sdk.orchestration.enums import ResourceType, ShareStatus
from gandal_sdk.orchestration.models import Page, ShareOut, ShareRevokeOut


class SharesApi:
    """Sous-client typé des partages."""

    def __init__(self, transport: HttpTransport) -> None:
        """Attache le transport HTTP partage."""
        self._http = transport

    def list(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> Page[ShareOut]:
        """Liste les partages des projets de l'appelant (extension)."""
        data = self._http.request(
            "GET",
            "/api/v1/shares",
            params={"page": page, "page_size": page_size},
        )
        return parse_page(data, ShareOut)

    def get(self, share_id: str) -> ShareOut:
        """Consulte un partage (extension)."""
        data = self._http.request("GET", f"/api/v1/shares/{share_id}")
        return ShareOut.model_validate(data)

    def list_for_project(
        self,
        project_id: str,
        *,
        page: int = 1,
        page_size: int = 20,
        resource_type: ResourceType | str | None = None,
        status: ShareStatus | str = ShareStatus.ACTIVE,
    ) -> Page[ShareOut]:
        """Liste les partages recus par un projet."""
        data = self._http.request(
            "GET",
            f"/api/v1/projects/{project_id}/shares",
            params=drop_none(
                {
                    "page": page,
                    "page_size": page_size,
                    "resource_type": resource_type,
                    "status": status,
                }
            ),
        )
        return parse_page(data, ShareOut)

    def revoke(self, share_id: str) -> ShareRevokeOut:
        """Revoque un partage actif."""
        data = self._http.request(
            "POST",
            f"/api/v1/shares/{share_id}/revoke",
        )
        return ShareRevokeOut.model_validate(data)
