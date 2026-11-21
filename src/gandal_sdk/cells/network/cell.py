"""Client de la cellule Reseau (agent_reseau / gandal_agent).

Sans endpoint configure, chaque methode leve CellUnavailable. Avec un endpoint,
les appels passent par POST /v1/<domaine> (corps check|apply) et renvoient une
NetworkExecution. L'en-tete Idempotency-Key est ignore par l'agent : l'empreinte
est calculee cote serveur sur le corps JSON.

Ne pas confondre avec client.orchestration.networks (metier iaas-api).
"""

from __future__ import annotations

from typing import Any, cast

from gandal_sdk._http import HttpTransport
from gandal_sdk.cells._base import not_ready
from gandal_sdk.cells.hypervisor import VmRef
from gandal_sdk.cells.network.models import (
    NetworkExecution,
    NetworkMode,
    NetworkRef,
    NetworkRequest,
)
from gandal_sdk.errors import GandalApiError, GandalError


def _route(domain: str) -> str:
    """xcpng.networks -> /v1/xcpng/networks (registre contracts.py de l'agent)."""
    return "/v1/" + domain.replace(".", "/")


def _vm_uuid(vm: str | VmRef) -> str:
    return vm if isinstance(vm, str) else vm.vm_id


class NetworkCell:
    """Client HTTP de l'agent reseau GANDAL."""

    def __init__(self, transport: HttpTransport | None = None) -> None:
        """Sans transport (endpoint non configure), chaque appel leve CellUnavailable."""
        self._http = transport

    def _transport(self) -> HttpTransport:
        if self._http is None:
            not_ready("network")
        return cast(HttpTransport, self._http)

    # --- socle ------------------------------------------------------------------

    def health(self) -> dict[str, Any]:
        """GET /v1/health - vie du processus (sans jeton, ne prouve pas XAPI/Kea)."""
        data = self._transport().request("GET", "/v1/health")
        return cast(dict[str, Any], data)

    def get_execution(self, execution_id: int) -> NetworkExecution:
        """Relit une execution (GET /v1/executions/{id}) sans la relancer."""
        data = self._transport().request("GET", f"/v1/executions/{execution_id}")
        return NetworkExecution.model_validate(data)

    def submit(self, operation: str, parameters: dict[str, Any]) -> NetworkExecution:
        """POST /v1/executions - enveloppe generique (operation + parameters)."""
        return self._post("/v1/executions", {"operation": operation, "parameters": parameters})

    def run(
        self,
        domain: str,
        action: str,
        spec: dict[str, Any] | None = None,
        *,
        target_id: str,
        mode: NetworkMode | str = NetworkMode.CHECK,
        schema_version: int = 1,
    ) -> NetworkExecution:
        """Execute une action d'un domaine (POST /v1/<domaine>).

        Toujours preferer mode=check avant mode=apply (contrat agent).
        """
        body = NetworkRequest(
            schema_version=schema_version,
            target_id=target_id,
            mode=mode,
            action=action,
            spec=dict(spec or {}),
        )
        return self._post(
            _route(domain),
            body.model_dump(mode="json"),
        )

    def require_succeeded(self, execution: NetworkExecution) -> NetworkExecution:
        """Leve GandalError si l'execution n'est pas SUCCEEDED."""
        if not execution.succeeded:
            raise GandalError(
                f"execution {execution.execution_id} en etat {execution.state} "
                f"(operation={execution.operation})"
            )
        return execution

    # --- alignement NetworkPort (EVPN / XCP-ng + vm-networks) --------------------

    def create_network(
        self,
        *,
        target_id: str,
        resource_key: str,
        name: str,
        mtu: int = 1500,
        mode: NetworkMode | str = NetworkMode.CHECK,
    ) -> NetworkExecution:
        """Cree un reseau interne XCP-ng (xcpng.networks / create_internal)."""
        return self.run(
            "xcpng.networks",
            "create_internal",
            {"resource_key": resource_key, "name": name, "mtu": mtu},
            target_id=target_id,
            mode=mode,
        )

    def rename_network(
        self,
        network: NetworkRef | str,
        name: str,
        *,
        target_id: str,
        description: str = "",
        mode: NetworkMode | str = NetworkMode.CHECK,
    ) -> NetworkExecution:
        """Renomme un reseau (xcpng.networks / update)."""
        network_uuid = network if isinstance(network, str) else network.network_id
        return self.run(
            "xcpng.networks",
            "update",
            {
                "network_uuid": network_uuid,
                "name": name,
                "description": description,
            },
            target_id=target_id,
            mode=mode,
        )

    def delete_network(
        self,
        network: NetworkRef | str,
        *,
        target_id: str,
        mode: NetworkMode | str = NetworkMode.CHECK,
    ) -> NetworkExecution:
        """Supprime un reseau XCP-ng (propriete gandal-owner requise cote agent)."""
        network_uuid = network if isinstance(network, str) else network.network_id
        return self.run(
            "xcpng.networks",
            "delete",
            {"network_uuid": network_uuid},
            target_id=target_id,
            mode=mode,
        )

    def attach_vm(
        self,
        network: NetworkRef | str,
        vm: str | VmRef,
        *,
        target_id: str,
        resource_key: str,
        user_uuid: str,
        hostname: str,
        mode: NetworkMode | str = NetworkMode.CHECK,
    ) -> NetworkExecution:
        """Rattache une VM a un reseau (vm-networks / add) - chemin EVPN.

        Pour l'architecture ACL (reseau USER unique), preferer user_vms(action='deploy').
        """
        network_uuid = network if isinstance(network, str) else network.network_id
        return self.run(
            "vm-networks",
            "add",
            {
                "resource_key": resource_key,
                "user_uuid": user_uuid,
                "vm_uuid": _vm_uuid(vm),
                "network_uuid": network_uuid,
                "hostname": hostname,
            },
            target_id=target_id,
            mode=mode,
        )

    def detach_vm(
        self,
        vm: str | VmRef,
        *,
        target_id: str,
        resource_key: str,
        user_uuid: str,
        vif_uuid: str,
        mode: NetworkMode | str = NetworkMode.CHECK,
    ) -> NetworkExecution:
        """Detache une VIF (vm-networks / remove) - met les IP en quarantaine."""
        return self.run(
            "vm-networks",
            "remove",
            {
                "resource_key": resource_key,
                "user_uuid": user_uuid,
                "vif_uuid": vif_uuid,
            },
            target_id=target_id,
            mode=mode,
        )

    def detach_vm_from_project(self, vm: str | VmRef, project_id: str) -> None:
        """Pas d'equivalent unique cote agent (ACL vs EVPN).

        Utiliser detach_vm (vm-networks remove) ou user_vms(isolate/…) selon
        l'architecture deployee.
        """
        raise GandalError(
            "detach_vm_from_project n'a pas d'operation unique sur l'agent reseau "
            f"(vm={_vm_uuid(vm)}, project={project_id}) : choisir vm-networks/remove "
            "ou user-vms selon l'architecture ACL/EVPN."
        )

    # --- raccourcis domaines frequents ------------------------------------------

    def user_vms(
        self,
        action: str,
        spec: dict[str, Any],
        *,
        target_id: str,
        mode: NetworkMode | str = NetworkMode.CHECK,
    ) -> NetworkExecution:
        """POST /v1/user-vms (architecture ACL, reseau USER)."""
        return self.run("user-vms", action, spec, target_id=target_id, mode=mode)

    def vm_acl(
        self,
        action: str,
        spec: dict[str, Any],
        *,
        target_id: str,
        mode: NetworkMode | str = NetworkMode.CHECK,
    ) -> NetworkExecution:
        """POST /v1/vm-acl (politique ACL par VM)."""
        return self.run("vm-acl", action, spec, target_id=target_id, mode=mode)

    def flows(
        self,
        action: str,
        spec: dict[str, Any] | None = None,
        *,
        target_id: str,
        mode: NetworkMode | str = NetworkMode.CHECK,
    ) -> NetworkExecution:
        """POST /v1/flows (flux inter-VM)."""
        return self.run("flows", action, spec, target_id=target_id, mode=mode)

    def xcpng(
        self,
        subdomain: str,
        action: str,
        spec: dict[str, Any] | None = None,
        *,
        target_id: str,
        mode: NetworkMode | str = NetworkMode.CHECK,
    ) -> NetworkExecution:
        """POST /v1/xcpng/<subdomain> (networks, vifs, vlans, pifs, bonds, inventory)."""
        return self.run(
            f"xcpng.{subdomain}",
            action,
            spec,
            target_id=target_id,
            mode=mode,
        )

    # --- interne ----------------------------------------------------------------

    def _post(self, path: str, body: dict[str, Any]) -> NetworkExecution:
        """POST et parse l'enveloppe ; 502/504 avec execution_id restent lisibles."""
        try:
            data = self._transport().request("POST", path, json=body)
        except GandalApiError as err:
            if err.status in {502, 504, 409} and isinstance(err.details, dict):
                if "execution_id" in err.details:
                    return NetworkExecution.model_validate(err.details)
            raise
        return NetworkExecution.model_validate(data)
