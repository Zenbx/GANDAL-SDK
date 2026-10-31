"""Helpers typés pour les espaces de stockage."""

from __future__ import annotations

from gandal_sdk._http import HttpTransport
from gandal_sdk.orchestration._util import delete_two_step, drop_none, parse_page
from gandal_sdk.orchestration.enums import StorageState
from gandal_sdk.orchestration.models import (
    DeletionOut,
    DeletionPreviewOut,
    Page,
    RequestOut,
    ShareCreateIn,
    ShareOut,
    StorageCreateRequestIn,
    StorageOut,
    StorageUpdateRequestIn,
)


class StoragesApi:
    """Sous-client typé /api/v1/projects/{id}/storages."""

    def __init__(self, transport: HttpTransport) -> None:
        """Attache le transport HTTP partage."""
        self._http = transport

    def list(
        self,
        project_id: str,
        *,
        page: int = 1,
        page_size: int = 20,
        state: StorageState | str | None = None,
        shared: bool | None = None,
        ip_address: str | None = None,
        name: str | None = None,
    ) -> Page[StorageOut]:
        """Liste les stockages visibles dans le projet."""
        data = self._http.request(
            "GET",
            f"/api/v1/projects/{project_id}/storages",
            params=drop_none(
                {
                    "page": page,
                    "page_size": page_size,
                    "state": state,
                    "shared": shared,
                    "ip_address": ip_address,
                    "name": name,
                }
            ),
        )
        return parse_page(data, StorageOut)

    def get(self, project_id: str, storage_id: str) -> StorageOut:
        """Consulte un stockage."""
        data = self._http.request(
            "GET",
            f"/api/v1/projects/{project_id}/storages/{storage_id}",
        )
        return StorageOut.model_validate(data)

    def request_create(
        self,
        project_id: str,
        body: StorageCreateRequestIn,
    ) -> RequestOut:
        """Depose une demande de creation de stockage."""
        data = self._http.request(
            "POST",
            f"/api/v1/projects/{project_id}/storages",
            json=body.model_dump(),
        )
        return RequestOut.model_validate(data)

    def request_update(
        self,
        project_id: str,
        storage_id: str,
        body: StorageUpdateRequestIn,
    ) -> RequestOut:
        """Depose une demande de redimensionnement."""
        data = self._http.request(
            "POST",
            f"/api/v1/projects/{project_id}/storages/{storage_id}/update-requests",
            json=body.model_dump(),
        )
        return RequestOut.model_validate(data)

    def delete(
        self,
        project_id: str,
        storage_id: str,
        *,
        confirmation_text: str | None = None,
        confirm: bool = False,
    ) -> DeletionPreviewOut | DeletionOut:
        """Supprime un stockage (protocole en deux temps)."""
        return delete_two_step(
            self._http,
            f"/api/v1/projects/{project_id}/storages/{storage_id}/deletion",
            confirmation_text=confirmation_text,
            confirm=confirm,
        )

    def share(
        self,
        project_id: str,
        storage_id: str,
        dest_project_id: str,
    ) -> ShareOut:
        """Partage un stockage vers un autre projet."""
        body = ShareCreateIn(dest_project_id=dest_project_id)
        data = self._http.request(
            "POST",
            f"/api/v1/projects/{project_id}/storages/{storage_id}/shares",
            json=body.model_dump(),
        )
        return ShareOut.model_validate(data)

    def list_shares(
        self,
        project_id: str,
        storage_id: str,
        *,
        page: int = 1,
        page_size: int = 20,
        status: str | None = None,
        dest_project_id: str | None = None,
    ) -> Page[ShareOut]:
        """Liste les partages emis pour un stockage."""
        data = self._http.request(
            "GET",
            f"/api/v1/projects/{project_id}/storages/{storage_id}/shares",
            params=drop_none(
                {
                    "page": page,
                    "page_size": page_size,
                    "status": status,
                    "dest_project_id": dest_project_id,
                }
            ),
        )
        return parse_page(data, ShareOut)
