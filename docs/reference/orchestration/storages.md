# Storages

Espaces de stockage projet.

**Acces :** `client.orchestration.storages`

!!! danger
    Le backend a retire une partie de ces routes : certains helpers peuvent renvoyer 404.

## `list`

```python
list(project_id: str, page: int, page_size: int, state: StorageState | str | None, shared: bool | None, ip_address: str | None, name: str | None) -> Page[StorageOut]
```

Liste les stockages visibles dans le projet.

**Route :** `GET /api/v1/projects/{project_id}/storages`, `GET /api/v1/projects/{project_id}/storages/{storage_id}`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `get`

```python
get(project_id: str, storage_id: str) -> StorageOut
```

Consulte un stockage.

**Route :** `GET /api/v1/projects/{project_id}/storages/{storage_id}`, `POST /api/v1/projects/{project_id}/storages`, `POST /api/v1/projects/{project_id}/storages/{storage_id}/update-requests`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `request_create`

```python
request_create(project_id: str, body: StorageCreateRequestIn) -> RequestOut
```

Depose une demande de creation de stockage.

**Route :** `POST /api/v1/projects/{project_id}/storages`, `POST /api/v1/projects/{project_id}/storages/{storage_id}/update-requests`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `request_update`

```python
request_update(project_id: str, storage_id: str, body: StorageUpdateRequestIn) -> RequestOut
```

Depose une demande de redimensionnement.

**Route :** `POST /api/v1/projects/{project_id}/storages/{storage_id}/update-requests`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `delete`

```python
delete(project_id: str, storage_id: str, confirmation_text: str | None, confirm: bool) -> DeletionPreviewOut | DeletionOut
```

Supprime un stockage (protocole en deux temps).

**Route :** `POST /api/v1/projects/{project_id}/storages/{storage_id}/shares`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `share`

```python
share(project_id: str, storage_id: str, dest_project_id: str) -> ShareOut
```

Partage un stockage vers un autre projet.

**Route :** `POST /api/v1/projects/{project_id}/storages/{storage_id}/shares`, `GET /api/v1/projects/{project_id}/storages/{storage_id}/shares`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `list_shares`

```python
list_shares(project_id: str, storage_id: str, page: int, page_size: int, status: str | None, dest_project_id: str | None) -> Page[ShareOut]
```

Liste les partages emis pour un stockage.

**Route :** `GET /api/v1/projects/{project_id}/storages/{storage_id}/shares`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `wait_until_deleted`

```python
wait_until_deleted(project_id: str, storage_id: str, delay: float, max_attempts: int) -> None
```

Attend que le stockage ne soit plus visible (404).

**Exceptions :** `GandalApiError` sur erreur HTTP metier.
