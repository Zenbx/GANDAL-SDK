# Profiles

Profils de droits et creation d'administrateurs.

**Acces :** `client.orchestration.profiles`

!!! warning
    `ProfileOut.id` et `profile_id` sont des **chaines**.

## `list_rights`

```python
list_rights() -> list[RightOut]
```

Liste le catalogue de droits.

**Route :** `GET /api/v1/admin/rights`, `GET /api/v1/admin/profiles`, `POST /api/v1/admin/profiles`, `PATCH /api/v1/admin/profiles/{profile_id}`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `list`

```python
list(page: int, page_size: int) -> Page[ProfileOut]
```

Liste les profils de droits.

**Route :** `GET /api/v1/admin/profiles`, `POST /api/v1/admin/profiles`, `PATCH /api/v1/admin/profiles/{profile_id}`, `DELETE /api/v1/admin/profiles/{profile_id}`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `create`

```python
create(body: ProfileCreateIn) -> ProfileOut
```

Cree un profil (administrateur).

**Route :** `POST /api/v1/admin/profiles`, `PATCH /api/v1/admin/profiles/{profile_id}`, `DELETE /api/v1/admin/profiles/{profile_id}`, `POST /api/v1/admin/admins`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `update`

```python
update(profile_id: str, body: ProfileUpdateIn) -> ProfileOut
```

Modifie un profil (administrateur).

**Route :** `PATCH /api/v1/admin/profiles/{profile_id}`, `DELETE /api/v1/admin/profiles/{profile_id}`, `POST /api/v1/admin/admins`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `delete`

```python
delete(profile_id: str) -> None
```

Supprime un profil (administrateur).

**Route :** `DELETE /api/v1/admin/profiles/{profile_id}`, `POST /api/v1/admin/admins`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `create_admin`

```python
create_admin(body: RegisterIn) -> IdentityOut
```

Cree un administrateur (POST /api/v1/admin/admins). Rend l'IDENTITE creee, pas un jeton : contrairement a `auth.register`, celui qui cree l'administrateur n'est pas celui qui l'utilisera. Rendre

**Route :** `POST /api/v1/admin/admins`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.
