"""Helpers typés pour les VMs d'un projet."""

from __future__ import annotations

from gandal_sdk._http import HttpTransport
from gandal_sdk.orchestration._util import delete_two_step, drop_none, parse_page
from gandal_sdk.orchestration.enums import PowerAction, VmState
from gandal_sdk.orchestration.models import (
    ConsoleOut,
    DeletionOut,
    DeletionPreviewOut,
    Page,
    PowerOut,
    RequestOut,
    ShareCreateIn,
    ShareOut,
    VMCreateRequestIn,
    VMOut,
    VMUpdateRequestIn,
)


class VmsApi:
    """Sous-client typé /api/v1/projects/{id}/vms."""

    def __init__(self, transport: HttpTransport) -> None:
        """Attache le transport HTTP partage."""
        self._http = transport

    def list(
        self,
        project_id: str,
        *,
        page: int = 1,
        page_size: int = 20,
        state: VmState | str | None = None,
        shared: bool | None = None,
        ip_address: str | None = None,
        name: str | None = None,
    ) -> Page[VMOut]:
        """Liste les VMs visibles dans le projet."""
        data = self._http.request(
            "GET",
            f"/api/v1/projects/{project_id}/vms",
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
        return parse_page(data, VMOut)

    def get(self, project_id: str, vm_id: str) -> VMOut:
        """Consulte une VM."""
        data = self._http.request(
            "GET",
            f"/api/v1/projects/{project_id}/vms/{vm_id}",
        )
        return VMOut.model_validate(data)

    def request_create(
        self,
        project_id: str,
        body: VMCreateRequestIn,
    ) -> RequestOut:
        """Depose une demande de creation de VM."""
        data = self._http.request(
            "POST",
            f"/api/v1/projects/{project_id}/vms",
            json=body.model_dump(exclude_none=True),
        )
        return RequestOut.model_validate(data)

    def request_update(
        self,
        project_id: str,
        vm_id: str,
        body: VMUpdateRequestIn,
    ) -> RequestOut:
        """Depose une demande de modification de VM."""
        data = self._http.request(
            "POST",
            f"/api/v1/projects/{project_id}/vms/{vm_id}/update-requests",
            json=body.model_dump(),
        )
        return RequestOut.model_validate(data)

    def power(
        self,
        project_id: str,
        vm_id: str,
        action: PowerAction | str,
    ) -> PowerOut:
        """Demarre, arrete ou redemarre une VM."""
        data = self._http.request(
            "POST",
            f"/api/v1/projects/{project_id}/vms/{vm_id}/power",
            json={"action": action},
        )
        return PowerOut.model_validate(data)

    def console(self, project_id: str, vm_id: str) -> ConsoleOut:
        """Ouvre un acces console."""
        data = self._http.request(
            "POST",
            f"/api/v1/projects/{project_id}/vms/{vm_id}/console",
        )
        return ConsoleOut.model_validate(data)

    def delete(
        self,
        project_id: str,
        vm_id: str,
        *,
        confirmation_text: str | None = None,
        confirm: bool = False,
    ) -> DeletionPreviewOut | DeletionOut:
        """Supprime une VM (protocole en deux temps)."""
        return delete_two_step(
            self._http,
            f"/api/v1/projects/{project_id}/vms/{vm_id}/deletion",
            confirmation_text=confirmation_text,
            confirm=confirm,
        )

    def share(
        self,
        project_id: str,
        vm_id: str,
        dest_project_id: str,
    ) -> ShareOut:
        """Partage une VM vers un autre projet."""
        body = ShareCreateIn(dest_project_id=dest_project_id)
        data = self._http.request(
            "POST",
            f"/api/v1/projects/{project_id}/vms/{vm_id}/shares",
            json=body.model_dump(),
        )
        return ShareOut.model_validate(data)

    def list_shares(
        self,
        project_id: str,
        vm_id: str,
        *,
        page: int = 1,
        page_size: int = 20,
        status: str | None = None,
        dest_project_id: str | None = None,
    ) -> Page[ShareOut]:
        """Liste les partages emis pour une VM."""
        data = self._http.request(
            "GET",
            f"/api/v1/projects/{project_id}/vms/{vm_id}/shares",
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
