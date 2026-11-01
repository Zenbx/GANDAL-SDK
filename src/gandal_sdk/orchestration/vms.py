"""Helpers typés pour les VMs d'un projet."""

from __future__ import annotations

from typing import cast

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
from gandal_sdk.waiters import DEFAULT_DELAY, DEFAULT_MAX_ATTEMPTS, wait_for

# Etats dont une VM ne sort pas d'elle-meme : attendre plus longtemps est inutile.
_VM_DEAD_ENDS = {VmState.ERROR, VmState.DELETING}


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

    def wait_until_running(
        self,
        project_id: str,
        vm_id: str,
        *,
        delay: float = DEFAULT_DELAY,
        max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    ) -> VMOut:
        """Attend l'etat running ; leve WaiterFailure si la VM passe en error ou deleting."""
        return self._wait_for_state(project_id, vm_id, VmState.RUNNING, delay, max_attempts)

    def wait_until_stopped(
        self,
        project_id: str,
        vm_id: str,
        *,
        delay: float = DEFAULT_DELAY,
        max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    ) -> VMOut:
        """Attend l'etat stopped ; leve WaiterFailure si la VM passe en error ou deleting."""
        return self._wait_for_state(project_id, vm_id, VmState.STOPPED, delay, max_attempts)

    def wait_until_deleted(
        self,
        project_id: str,
        vm_id: str,
        *,
        delay: float = DEFAULT_DELAY,
        max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    ) -> None:
        """Attend que la VM ne soit plus visible (404) ; leve WaiterFailure sur error."""
        wait_for(
            lambda: self.get(project_id, vm_id),
            is_success=lambda _: False,
            failure_reason=lambda vm: (
                "la suppression a echoue (etat error)" if vm.state == VmState.ERROR else None
            ),
            gone_is_success=True,
            description=f"Suppression de la VM {vm_id}",
            delay=delay,
            max_attempts=max_attempts,
            sleep=self._http.sleep,
        )

    def _wait_for_state(
        self,
        project_id: str,
        vm_id: str,
        target: VmState,
        delay: float,
        max_attempts: int,
    ) -> VMOut:
        """Attend target ; unknown n'est jamais un succes (API_ENDPOINTS.md §2.3)."""
        vm = wait_for(
            lambda: self.get(project_id, vm_id),
            is_success=lambda vm: vm.state == target,
            failure_reason=lambda vm: (
                f"etat {vm.state} au lieu de {target}" if vm.state in _VM_DEAD_ENDS else None
            ),
            description=f"VM {vm_id}",
            delay=delay,
            max_attempts=max_attempts,
            sleep=self._http.sleep,
        )
        # gone_is_success desactive : wait_for ne renvoie jamais GONE ici.
        return cast(VMOut, vm)
