# Reseau

Agent reseau (executions /v1, check|apply). Contrat : agent_reseau docs/endpoints.

**Acces :** `client.network`

!!! warning
    Sans cell_urls['network'] / GANDAL_NETWORK_ENDPOINT, CellUnavailable.

!!! note
    Metier projet : `client.orchestration.networks`. Toujours `check` avant `apply`.

## `health`

```python
health() -> dict[str, Any]
```

GET /v1/health - vie du processus (sans jeton, ne prouve pas XAPI/Kea).

**Route :** `GET /v1/health`, `GET /v1/executions/{execution_id}`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `get_execution`

```python
get_execution(execution_id: int) -> NetworkExecution
```

Relit une execution (GET /v1/executions/{id}) sans la relancer.

**Route :** `GET /v1/executions/{execution_id}`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `submit`

```python
submit(operation: str, parameters: dict[str, Any]) -> NetworkExecution
```

POST /v1/executions - enveloppe generique (operation + parameters).

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `run`

```python
run(domain: str, action: str, spec: dict[str, Any] | None = None, target_id: str, mode: NetworkMode | str, schema_version: int) -> NetworkExecution
```

Execute une action d'un domaine (POST /v1/<domaine>). Toujours preferer mode=check avant mode=apply (contrat agent).

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `require_succeeded`

```python
require_succeeded(execution: NetworkExecution) -> NetworkExecution
```

Leve GandalError si l'execution n'est pas SUCCEEDED.

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `create_network`

```python
create_network(target_id: str, resource_key: str, name: str, mtu: int, mode: NetworkMode | str) -> NetworkExecution
```

Cree un reseau interne XCP-ng (xcpng.networks / create_internal).

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `rename_network`

```python
rename_network(network: NetworkRef | str, name: str, target_id: str, description: str, mode: NetworkMode | str) -> NetworkExecution
```

Renomme un reseau (xcpng.networks / update).

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `delete_network`

```python
delete_network(network: NetworkRef | str, target_id: str, mode: NetworkMode | str) -> NetworkExecution
```

Supprime un reseau XCP-ng (propriete gandal-owner requise cote agent).

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `attach_vm`

```python
attach_vm(network: NetworkRef | str, vm: str | VmRef, target_id: str, resource_key: str, user_uuid: str, hostname: str, mode: NetworkMode | str) -> NetworkExecution
```

Rattache une VM a un reseau (vm-networks / add) - chemin EVPN. Pour l'architecture ACL (reseau USER unique), preferer user_vms(action='deploy').

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `detach_vm`

```python
detach_vm(vm: str | VmRef, target_id: str, resource_key: str, user_uuid: str, vif_uuid: str, mode: NetworkMode | str) -> NetworkExecution
```

Detache une VIF (vm-networks / remove) - met les IP en quarantaine.

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `detach_vm_from_project`

```python
detach_vm_from_project(vm: str | VmRef, project_id: str) -> None
```

Pas d'equivalent unique cote agent (ACL vs EVPN). Utiliser detach_vm (vm-networks remove) ou user_vms(isolate/…) selon l'architecture deployee.

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `user_vms`

```python
user_vms(action: str, spec: dict[str, Any], target_id: str, mode: NetworkMode | str) -> NetworkExecution
```

POST /v1/user-vms (architecture ACL, reseau USER).

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `vm_acl`

```python
vm_acl(action: str, spec: dict[str, Any], target_id: str, mode: NetworkMode | str) -> NetworkExecution
```

POST /v1/vm-acl (politique ACL par VM).

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `flows`

```python
flows(action: str, spec: dict[str, Any] | None = None, target_id: str, mode: NetworkMode | str) -> NetworkExecution
```

POST /v1/flows (flux inter-VM).

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `xcpng`

```python
xcpng(subdomain: str, action: str, spec: dict[str, Any] | None = None, target_id: str, mode: NetworkMode | str) -> NetworkExecution
```

POST /v1/xcpng/<subdomain> (networks, vifs, vlans, pifs, bonds, inventory).

**Exceptions :** `GandalApiError` sur erreur HTTP metier.
