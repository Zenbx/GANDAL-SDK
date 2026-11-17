# VMs

Machines virtuelles d'un projet : demandes, alimentation, partage, suppression.

**Acces :** `client.orchestration.vms`

!!! note
    Creation et modification passent par une **demande** admin (`request_create` / `request_update`), pas un create direct.

## `list`

```python
list(project_id: str, page: int, page_size: int, state: VmState | str | None, shared: bool | None, ip_address: str | None, name: str | None) -> Page[VMOut]
```

Liste les VMs visibles dans le projet.

**Route :** `GET /api/v1/projects/{project_id}/vms`, `GET /api/v1/projects/{project_id}/vms/{vm_id}`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `get`

```python
get(project_id: str, vm_id: str) -> VMOut
```

Consulte une VM.

**Route :** `GET /api/v1/projects/{project_id}/vms/{vm_id}`, `POST /api/v1/projects/{project_id}/vms`, `POST /api/v1/projects/{project_id}/vms/{vm_id}/update-requests`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `request_create`

```python
request_create(project_id: str, body: VMCreateRequestIn) -> RequestOut
```

Depose une demande de creation de VM.

**Route :** `POST /api/v1/projects/{project_id}/vms`, `POST /api/v1/projects/{project_id}/vms/{vm_id}/update-requests`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `request_update`

```python
request_update(project_id: str, vm_id: str, body: VMUpdateRequestIn) -> RequestOut
```

Depose une demande de modification de VM.

**Route :** `POST /api/v1/projects/{project_id}/vms/{vm_id}/update-requests`, `POST /api/v1/projects/{project_id}/vms/{vm_id}/power`, `POST /api/v1/projects/{project_id}/vms/{vm_id}/console`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `power`

```python
power(project_id: str, vm_id: str, action: PowerAction | str) -> PowerOut
```

Demarre, arrete ou redemarre une VM.

**Route :** `POST /api/v1/projects/{project_id}/vms/{vm_id}/power`, `POST /api/v1/projects/{project_id}/vms/{vm_id}/console`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `console`

```python
console(project_id: str, vm_id: str) -> ConsoleOut
```

Ouvre un acces console.

**Route :** `POST /api/v1/projects/{project_id}/vms/{vm_id}/console`, `POST /api/v1/projects/{project_id}/vms/{vm_id}/shares`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `delete`

```python
delete(project_id: str, vm_id: str, confirmation_text: str | None, confirm: bool) -> DeletionPreviewOut | DeletionOut
```

Supprime une VM (protocole en deux temps).

**Route :** `POST /api/v1/projects/{project_id}/vms/{vm_id}/shares`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `share`

```python
share(project_id: str, vm_id: str, dest_project_id: str) -> ShareOut
```

Partage une VM vers un autre projet.

**Route :** `POST /api/v1/projects/{project_id}/vms/{vm_id}/shares`, `GET /api/v1/projects/{project_id}/vms/{vm_id}/shares`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `list_shares`

```python
list_shares(project_id: str, vm_id: str, page: int, page_size: int, status: str | None, dest_project_id: str | None) -> Page[ShareOut]
```

Liste les partages emis pour une VM.

**Route :** `GET /api/v1/projects/{project_id}/vms/{vm_id}/shares`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `wait_until_running`

```python
wait_until_running(project_id: str, vm_id: str, delay: float, max_attempts: int) -> VMOut
```

Attend l'etat running ; leve WaiterFailure si la VM passe en error ou deleting.

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `wait_until_stopped`

```python
wait_until_stopped(project_id: str, vm_id: str, delay: float, max_attempts: int) -> VMOut
```

Attend l'etat stopped ; leve WaiterFailure si la VM passe en error ou deleting.

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `wait_until_deleted`

```python
wait_until_deleted(project_id: str, vm_id: str, delay: float, max_attempts: int) -> None
```

Attend que la VM ne soit plus visible (404) ; leve WaiterFailure sur error.

**Exceptions :** `GandalApiError` sur erreur HTTP metier.
