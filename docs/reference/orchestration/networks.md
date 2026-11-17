# Networks

Reseaux d'un projet et rattachement de VM.

**Acces :** `client.orchestration.networks`

## `list`

```python
list(project_id: str, page: int, page_size: int, name: str | None) -> Page[NetworkOut]
```

Liste les reseaux du projet.

**Route :** `GET /api/v1/projects/{project_id}/networks`, `GET /api/v1/projects/{project_id}/networks/{network_id}`, `POST /api/v1/projects/{project_id}/networks`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `get`

```python
get(project_id: str, network_id: str) -> NetworkOut
```

Lit un reseau.

**Route :** `GET /api/v1/projects/{project_id}/networks/{network_id}`, `POST /api/v1/projects/{project_id}/networks`, `PATCH /api/v1/projects/{project_id}/networks/{network_id}`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `create`

```python
create(project_id: str, name: str) -> NetworkOut
```

Cree un reseau.

**Route :** `POST /api/v1/projects/{project_id}/networks`, `PATCH /api/v1/projects/{project_id}/networks/{network_id}`, `POST /api/v1/projects/{project_id}/networks/{network_id}/vms`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `rename`

```python
rename(project_id: str, network_id: str, name: str) -> NetworkOut
```

Renomme un reseau.

**Route :** `PATCH /api/v1/projects/{project_id}/networks/{network_id}`, `POST /api/v1/projects/{project_id}/networks/{network_id}/vms`, `DELETE /api/v1/projects/{project_id}/networks/{network_id}/vms/{vm_id}`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `attach_vm`

```python
attach_vm(project_id: str, network_id: str, vm_id: str) -> NetworkOut
```

Rattache une VM au reseau.

**Route :** `POST /api/v1/projects/{project_id}/networks/{network_id}/vms`, `DELETE /api/v1/projects/{project_id}/networks/{network_id}/vms/{vm_id}`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `detach_vm`

```python
detach_vm(project_id: str, network_id: str, vm_id: str) -> NetworkOut
```

Retire une VM du reseau.

**Route :** `DELETE /api/v1/projects/{project_id}/networks/{network_id}/vms/{vm_id}`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `delete`

```python
delete(project_id: str, network_id: str, confirmation_text: str | None, confirm: bool) -> DeletionPreviewOut | DeletionOut
```

Supprime un reseau (protocole en deux temps).

**Exceptions :** `GandalApiError` sur erreur HTTP metier.
