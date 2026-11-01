"""Client de la cellule Hyperviseur (service gandal-hypervisor).

Sans endpoint configure, chaque methode leve CellUnavailable. Avec un endpoint,
les ecritures renvoient une operation (docs/CONVENTIONS_API.md §7) et les
waiters attendent l'etat voulu de la VM.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any, cast

from pydantic import BaseModel

from gandal_sdk._http import HttpTransport
from gandal_sdk.cells._base import not_ready
from gandal_sdk.orchestration.enums import VmState
from gandal_sdk.waiters import DEFAULT_DELAY, DEFAULT_MAX_ATTEMPTS, wait_for


class PowerAction(StrEnum):
    """Action d'alimentation d'une VM."""

    START = "start"
    STOP = "stop"
    RESTART = "restart"


@dataclass(frozen=True)
class VmSpec:
    """Caracteristiques demandees a l'hyperviseur."""

    name: str
    ram_gb: int
    vcpu: int
    vram_gb: int
    ssd_gb: int


@dataclass(frozen=True)
class VmRef:
    """Reference d'une VM cote hyperviseur."""

    vm_id: str
    ip_address: str | None = None


@dataclass(frozen=True)
class ConsoleAccess:
    """Acces console graphique temporaire."""

    url: str
    expires_in: int


class OperationStatus(StrEnum):
    """Etat d'une operation longue de la cellule."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class CellError(BaseModel):
    """Erreur d'une operation echouee, au format {code, message, details}."""

    code: str
    message: str
    details: Any = None


class CellOperation(BaseModel):
    """Operation longue de la cellule."""

    id: str
    action: str
    vm_id: str
    status: OperationStatus
    error: CellError | None = None
    created_at: datetime
    updated_at: datetime


class HypervisorVm(BaseModel):
    """VM vue par la cellule ; xapi_uuid est l'identifiant XCP-ng sous-jacent."""

    vm_id: str
    name: str
    state: VmState
    ip_address: str | None = None
    ram_gb: int | None = None
    vcpu: int | None = None
    ssd_gb: int | None = None
    host: str | None = None
    xapi_uuid: str | None = None

    @property
    def ref(self) -> VmRef:
        return VmRef(vm_id=self.vm_id, ip_address=self.ip_address)


class CellHealth(BaseModel):
    """Etat de la cellule et maitre du pool qu'elle joint."""

    status: str
    pool_master: str
    version: str


class CreatedVm(BaseModel):
    """Reponse a une creation : la VM (etat creating) et son operation."""

    vm: HypervisorVm
    operation: CellOperation


# Etats dont une VM ne sort pas d'elle-meme quand on attend running ou stopped.
_DEAD_ENDS = {VmState.ERROR, VmState.DELETING}


def _vm_id(vm: str | VmRef | HypervisorVm) -> str:
    return vm if isinstance(vm, str) else vm.vm_id


class HypervisorCell:
    """Client de la cellule Hyperviseur."""

    def __init__(self, transport: HttpTransport | None = None) -> None:
        """Sans transport (endpoint non configure), chaque appel leve CellUnavailable."""
        self._http = transport

    def _transport(self) -> HttpTransport:
        if self._http is None:
            not_ready("hypervisor")
        return cast(HttpTransport, self._http)

    # --- lecture ----------------------------------------------------------------

    def health(self) -> CellHealth:
        """Leve GandalApiError upstream_unavailable (503) si le pool ne repond pas."""
        return CellHealth.model_validate(self._transport().request("GET", "/health"))

    def list_vms(self) -> list[HypervisorVm]:
        """VM gerees par la cellule (les autres VM du pool n'y figurent jamais)."""
        data = self._transport().request("GET", "/v1/vms")
        return [HypervisorVm.model_validate(item) for item in data["items"]]

    def get_vm(self, vm: str | VmRef | HypervisorVm) -> HypervisorVm:
        data = self._transport().request("GET", f"/v1/vms/{_vm_id(vm)}")
        return HypervisorVm.model_validate(data)

    def get_operation(self, operation_id: str) -> CellOperation:
        data = self._transport().request("GET", f"/v1/operations/{operation_id}")
        return CellOperation.model_validate(data)

    # --- ecriture ---------------------------------------------------------------

    def create_vm(self, spec: VmSpec) -> CreatedVm:
        """Lance la creation ; la VM est renvoyee aussitot en etat creating."""
        data = self._transport().request("POST", "/v1/vms", json=asdict(spec))
        return CreatedVm.model_validate(data)

    def update_vm(self, vm: str | VmRef | HypervisorVm, spec: VmSpec) -> CellOperation:
        """Modifie vCPU, memoire et disque ; la VM doit etre arretee."""
        data = self._transport().request("PUT", f"/v1/vms/{_vm_id(vm)}", json=asdict(spec))
        return CellOperation.model_validate(data["operation"])

    def power(self, vm: str | VmRef | HypervisorVm, action: PowerAction | str) -> CellOperation:
        data = self._transport().request(
            "POST", f"/v1/vms/{_vm_id(vm)}/power", json={"action": str(action)}
        )
        return CellOperation.model_validate(data["operation"])

    def console(self, vm: str | VmRef | HypervisorVm) -> ConsoleAccess:
        """Acces console ; la cellule repond aujourd'hui not_implemented (501)."""
        data = self._transport().request("POST", f"/v1/vms/{_vm_id(vm)}/console")
        return ConsoleAccess(url=data["url"], expires_in=data["expires_in"])

    def delete_vm(self, vm: str | VmRef | HypervisorVm) -> CellOperation:
        data = self._transport().request("DELETE", f"/v1/vms/{_vm_id(vm)}")
        return CellOperation.model_validate(data["operation"])

    # --- attentes ---------------------------------------------------------------

    def wait_for_operation(
        self,
        operation: str | CellOperation,
        *,
        delay: float = DEFAULT_DELAY,
        max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    ) -> CellOperation:
        """Attend la fin d'une operation ; leve WaiterFailure si elle echoue."""
        operation_id = operation if isinstance(operation, str) else operation.id
        result = wait_for(
            lambda: self.get_operation(operation_id),
            is_success=lambda op: op.status == OperationStatus.SUCCEEDED,
            failure_reason=lambda op: (
                f"{op.error.code} : {op.error.message}"
                if op.status == OperationStatus.FAILED and op.error
                else ("echec" if op.status == OperationStatus.FAILED else None)
            ),
            description=f"Operation {operation_id}",
            delay=delay,
            max_attempts=max_attempts,
            sleep=self._transport().sleep,
        )
        return cast(CellOperation, result)

    def wait_until_running(
        self,
        vm: str | VmRef | HypervisorVm,
        *,
        delay: float = DEFAULT_DELAY,
        max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    ) -> HypervisorVm:
        """Attend running ; leve WaiterFailure sur error ou deleting."""
        return self._wait_for_state(_vm_id(vm), VmState.RUNNING, delay, max_attempts)

    def wait_until_stopped(
        self,
        vm: str | VmRef | HypervisorVm,
        *,
        delay: float = DEFAULT_DELAY,
        max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    ) -> HypervisorVm:
        """Attend stopped ; leve WaiterFailure sur error ou deleting."""
        return self._wait_for_state(_vm_id(vm), VmState.STOPPED, delay, max_attempts)

    def wait_until_deleted(
        self,
        vm: str | VmRef | HypervisorVm,
        *,
        delay: float = DEFAULT_DELAY,
        max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    ) -> None:
        """Attend que la VM ne soit plus visible (404) ; leve WaiterFailure sur error."""
        vm_id = _vm_id(vm)
        wait_for(
            lambda: self.get_vm(vm_id),
            is_success=lambda _: False,
            failure_reason=lambda found: (
                "la suppression a echoue (etat error)" if found.state == VmState.ERROR else None
            ),
            gone_is_success=True,
            description=f"Suppression de la VM {vm_id}",
            delay=delay,
            max_attempts=max_attempts,
            sleep=self._transport().sleep,
        )

    def _wait_for_state(
        self, vm_id: str, target: VmState, delay: float, max_attempts: int
    ) -> HypervisorVm:
        found = wait_for(
            lambda: self.get_vm(vm_id),
            is_success=lambda vm: vm.state == target,
            failure_reason=lambda vm: (
                f"etat {vm.state} au lieu de {target}" if vm.state in _DEAD_ENDS else None
            ),
            description=f"VM {vm_id}",
            delay=delay,
            max_attempts=max_attempts,
            sleep=self._transport().sleep,
        )
        return cast(HypervisorVm, found)
