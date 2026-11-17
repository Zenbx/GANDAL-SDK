# Auth (orchestration)

Sous-client d'identite de l'API d'orchestration.

**Acces :** `client.orchestration.auth`

## `register`

```python
register(body: 'RegisterIn') -> TokenOut
```

Cree un compte et rend son jeton (POST /api/v1/auth/register). Le jeton est pose sur le transport, comme pour `login` : apres une inscription, l'appelant est connecte. Ne pas le poser obligerait chaque

**Route :** `POST /api/v1/auth/register`, `POST /api/v1/auth/login`, `GET /api/v1/auth/me`, `PATCH /api/v1/auth/me`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `login`

```python
login(email: str, password: str) -> TokenOut
```

Echange email/mot de passe contre un jeton Bearer.

**Route :** `POST /api/v1/auth/login`, `GET /api/v1/auth/me`, `PATCH /api/v1/auth/me`, `POST /api/v1/auth/password`, `DELETE /api/v1/auth/me`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `me`

```python
me() -> IdentityOut
```

Lit l'identite associee au jeton courant.

**Route :** `GET /api/v1/auth/me`, `PATCH /api/v1/auth/me`, `POST /api/v1/auth/password`, `DELETE /api/v1/auth/me`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `update_me`

```python
update_me(body: UserUpdateIn) -> TokenOut
```

Met a jour l'identite et conserve le nouveau jeton.

**Route :** `PATCH /api/v1/auth/me`, `POST /api/v1/auth/password`, `DELETE /api/v1/auth/me`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `change_password`

```python
change_password(old_password: str, new_password: str) -> None
```

Remplace le mot de passe apres verification de l'ancien.

**Route :** `POST /api/v1/auth/password`, `DELETE /api/v1/auth/me`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `delete_me`

```python
delete_me() -> None
```

Supprime le compte courant.

**Route :** `DELETE /api/v1/auth/me`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.
