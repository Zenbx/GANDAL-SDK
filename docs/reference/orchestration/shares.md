# Shares

Partages de ressources entre projets.

**Acces :** `client.orchestration.shares`

## `list`

```python
list(page: int, page_size: int) -> Page[ShareOut]
```

Liste les partages des projets de l'appelant (extension).

**Route :** `GET /api/v1/shares`, `GET /api/v1/shares/{share_id}`, `GET /api/v1/projects/{project_id}/shares`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `get`

```python
get(share_id: str) -> ShareOut
```

Consulte un partage (extension).

**Route :** `GET /api/v1/shares/{share_id}`, `GET /api/v1/projects/{project_id}/shares`, `POST /api/v1/shares/{share_id}/revoke`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `list_for_project`

```python
list_for_project(project_id: str, page: int, page_size: int, resource_type: ResourceType | str | None, status: ShareStatus | str) -> Page[ShareOut]
```

Liste les partages recus par un projet.

**Route :** `GET /api/v1/projects/{project_id}/shares`, `POST /api/v1/shares/{share_id}/revoke`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `revoke`

```python
revoke(share_id: str) -> ShareRevokeOut
```

Revoque un partage actif.

**Route :** `POST /api/v1/shares/{share_id}/revoke`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.
