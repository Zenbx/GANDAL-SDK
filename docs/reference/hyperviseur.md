# Hyperviseur

Pilotage des VM du pool via la cellule gandal-hypervisor.

**Acces :** `client.hypervisor`

!!! warning
    Sans `cell_urls['hypervisor']` / `GANDAL_HYPERVISOR_ENDPOINT`, `CellUnavailable`.

## `health`

```python
health() -> CellHealth
```

Leve GandalApiError upstream_unavailable (503) si le pool ne repond pas.

**Route :** `GET /health`, `GET /v1/vms`, `GET /v1/vms/{_vm_id(vm)}`, `GET /v1/operations/{operation_id}`, `POST /v1/vms`, `PUT /v1/vms/{_vm_id(vm)}`, `POST /v1/vms/{_vm_id(vm)}/power`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `list_vms`

```python
list_vms() -> list[HypervisorVm]
```

VM gerees par la cellule (les autres VM du pool n'y figurent jamais).

**Route :** `GET /v1/vms`, `GET /v1/vms/{_vm_id(vm)}`, `GET /v1/operations/{operation_id}`, `POST /v1/vms`, `PUT /v1/vms/{_vm_id(vm)}`, `POST /v1/vms/{_vm_id(vm)}/power`, `POST /v1/vms/{_vm_id(vm)}/console`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `get_vm`

```python
get_vm(vm: str | VmRef | HypervisorVm) -> HypervisorVm
```

**Route :** `GET /v1/vms/{_vm_id(vm)}`, `GET /v1/operations/{operation_id}`, `POST /v1/vms`, `PUT /v1/vms/{_vm_id(vm)}`, `POST /v1/vms/{_vm_id(vm)}/power`, `POST /v1/vms/{_vm_id(vm)}/console`, `DELETE /v1/vms/{_vm_id(vm)}`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `get_operation`

```python
get_operation(operation_id: str) -> CellOperation
```

**Route :** `GET /v1/operations/{operation_id}`, `POST /v1/vms`, `PUT /v1/vms/{_vm_id(vm)}`, `POST /v1/vms/{_vm_id(vm)}/power`, `POST /v1/vms/{_vm_id(vm)}/console`, `DELETE /v1/vms/{_vm_id(vm)}`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `create_vm`

```python
create_vm(spec: VmSpec) -> CreatedVm
```

Lance la creation ; la VM est renvoyee aussitot en etat creating.

**Route :** `POST /v1/vms`, `PUT /v1/vms/{_vm_id(vm)}`, `POST /v1/vms/{_vm_id(vm)}/power`, `POST /v1/vms/{_vm_id(vm)}/console`, `DELETE /v1/vms/{_vm_id(vm)}`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `update_vm`

```python
update_vm(vm: str | VmRef | HypervisorVm, spec: VmSpec) -> CellOperation
```

Modifie vCPU, memoire et disque ; la VM doit etre arretee.

**Route :** `PUT /v1/vms/{_vm_id(vm)}`, `POST /v1/vms/{_vm_id(vm)}/power`, `POST /v1/vms/{_vm_id(vm)}/console`, `DELETE /v1/vms/{_vm_id(vm)}`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `power`

```python
power(vm: str | VmRef | HypervisorVm, action: PowerAction | str) -> CellOperation
```

**Route :** `POST /v1/vms/{_vm_id(vm)}/power`, `POST /v1/vms/{_vm_id(vm)}/console`, `DELETE /v1/vms/{_vm_id(vm)}`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `console`

```python
console(vm: str | VmRef | HypervisorVm) -> ConsoleAccess
```

Acces console ; la cellule repond aujourd'hui not_implemented (501).

**Route :** `POST /v1/vms/{_vm_id(vm)}/console`, `DELETE /v1/vms/{_vm_id(vm)}`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `delete_vm`

```python
delete_vm(vm: str | VmRef | HypervisorVm) -> CellOperation
```

**Route :** `DELETE /v1/vms/{_vm_id(vm)}`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `wait_for_operation`

```python
wait_for_operation(operation: str | CellOperation, delay: float, max_attempts: int) -> CellOperation
```

Attend la fin d'une operation ; leve WaiterFailure si elle echoue.

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `wait_until_running`

```python
wait_until_running(vm: str | VmRef | HypervisorVm, delay: float, max_attempts: int) -> HypervisorVm
```

Attend running ; leve WaiterFailure sur error ou deleting.

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `wait_until_stopped`

```python
wait_until_stopped(vm: str | VmRef | HypervisorVm, delay: float, max_attempts: int) -> HypervisorVm
```

Attend stopped ; leve WaiterFailure sur error ou deleting.

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `wait_until_deleted`

```python
wait_until_deleted(vm: str | VmRef | HypervisorVm, delay: float, max_attempts: int) -> None
```

Attend que la VM ne soit plus visible (404) ; leve WaiterFailure sur error.

**Exceptions :** `GandalApiError` sur erreur HTTP metier.
