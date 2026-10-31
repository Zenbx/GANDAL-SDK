"""Helpers typés pour les reseaux d'un projet."""

from __future__ import annotations

from gandal_sdk._http import HttpTransport
from gandal_sdk.orchestration._util import delete_two_step, drop_none, parse_page
from gandal_sdk.orchestration.models import (
    DeletionOut,
    DeletionPreviewOut,
    NetworkCreateIn,
    NetworkOut,
    NetworkUpdateIn,
    Page,
)


class NetworksApi:
    """Sous-client typé /api/v1/projects/{id}/networks."""

    def __init__(self, transport: HttpTransport) -> None:
        """Attache le transport HTTP partage."""
        self._http = transport

    def list(
        self,
        project_id: str,
        *,
        page: int = 1,
        page_size: int = 20,
        name: str | None = None,
    ) -> Page[NetworkOut]:
        """Liste les reseaux du projet."""
        data = self._http.request(
            "GET",
            f"/api/v1/projects/{project_id}/networks",
            params=drop_none(
                {"page": page, "page_size": page_size, "name": name}
            ),
        )
        return parse_page(data, NetworkOut)

    def get(self, project_id: str, network_id: str) -> NetworkOut:
        """Lit un reseau."""
        data = self._http.request(
            "GET",
            f"/api/v1/projects/{project_id}/networks/{network_id}",
        )
        return NetworkOut.model_validate(data)

    def create(self, project_id: str, name: str) -> NetworkOut:
        """Cree un reseau."""
        body = NetworkCreateIn(name=name)
        data = self._http.request(
            "POST",
            f"/api/v1/projects/{project_id}/networks",
            json=body.model_dump(),
        )
        return NetworkOut.model_validate(data)

    def rename(self, project_id: str, network_id: str, name: str) -> NetworkOut:
        """Renomme un reseau."""
        body = NetworkUpdateIn(name=name)
        data = self._http.request(
            "PATCH",
            f"/api/v1/projects/{project_id}/networks/{network_id}",
            json=body.model_dump(),
        )
        return NetworkOut.model_validate(data)

    def attach_vm(
        self,
        project_id: str,
        network_id: str,
        vm_id: str,
    ) -> NetworkOut:
        """Rattache une VM au reseau."""
        data = self._http.request(
            "POST",
            f"/api/v1/projects/{project_id}/networks/{network_id}/vms",
            json={"vm_id": vm_id},
        )
        return NetworkOut.model_validate(data)

    def detach_vm(
        self,
        project_id: str,
        network_id: str,
        vm_id: str,
    ) -> NetworkOut:
        """Retire une VM du reseau."""
        data = self._http.request(
            "DELETE",
            f"/api/v1/projects/{project_id}/networks/{network_id}/vms/{vm_id}",
        )
        return NetworkOut.model_validate(data)

    def delete(
        self,
        project_id: str,
        network_id: str,
        *,
        confirmation_text: str | None = None,
        confirm: bool = False,
    ) -> DeletionPreviewOut | DeletionOut:
        """Supprime un reseau (protocole en deux temps)."""
        return delete_two_step(
            self._http,
            f"/api/v1/projects/{project_id}/networks/{network_id}/deletion",
            confirmation_text=confirmation_text,
            confirm=confirm,
        )
