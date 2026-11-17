# Packs

Catalogue de packs (lecture) et administration.

**Acces :** `client.orchestration.packs`

## `list`

```python
list(page: int, page_size: int, name: str | None, min_ram_gb: int | None, max_ram_gb: int | None, min_vcpu: int | None, max_vcpu: int | None) -> Page[PackOut]
```

Liste le catalogue de packs.

**Route :** `GET /api/v1/packs`, `GET /api/v1/packs/{pack_id}`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `get`

```python
get(pack_id: str) -> PackOut
```

Lit un pack.

**Route :** `GET /api/v1/packs/{pack_id}`, `POST /api/v1/admin/packs`, `PATCH /api/v1/admin/packs/{pack_id}`, `DELETE /api/v1/admin/packs/{pack_id}`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `create`

```python
create(body: PackCreateIn) -> PackOut
```

Cree un pack (administrateur).

**Route :** `POST /api/v1/admin/packs`, `PATCH /api/v1/admin/packs/{pack_id}`, `DELETE /api/v1/admin/packs/{pack_id}`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `update`

```python
update(pack_id: str, body: PackUpdateIn) -> PackOut
```

Modifie un pack (administrateur).

**Route :** `PATCH /api/v1/admin/packs/{pack_id}`, `DELETE /api/v1/admin/packs/{pack_id}`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `delete`

```python
delete(pack_id: str) -> None
```

Supprime un pack (administrateur).

**Route :** `DELETE /api/v1/admin/packs/{pack_id}`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.
