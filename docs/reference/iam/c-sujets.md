# C - Sujets, roles, audit

Identites, quotas sujets, roles, journal.

**Acces :** `client.iam`

!!! note
    Sans endpoint IAM configure, chaque appel leve `CellUnavailable`. Les ecritures envoient une `Idempotency-Key` (sauf `create_access_key` et `assume_role`). Erreurs en `application/problem+json` → `GandalApiError`.

## `list_subjects`

```python
list_subjects(curseur: str | None, taille: int | None, correlation_id: str | None) -> m.PageSujets
```

Liste paginee des sujets.

**Route :** `GET /subjects`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `create_subject`

```python
create_subject(identifiant: str, courriel: str | None, prenom: str | None, nom: str | None, groupes: list[str] | None, externe: bool | None, expire_a: str | None, idempotency_key: str | None, correlation_id: str | None) -> m.Sujet
```

Cree un sujet (compte).

**Route :** `POST /subjects`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `get_me`

```python
get_me(correlation_id: str | None) -> m.Sujet
```

Sujet correspondant au jeton courant.

**Route :** `GET /subjects/me`, `GET /subjects/{subject_id}`, `DELETE /subjects/{subject_id}`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `get_subject`

```python
get_subject(subject_id: str, correlation_id: str | None) -> m.Sujet
```

Lit un sujet par identifiant.

**Route :** `GET /subjects/{subject_id}`, `DELETE /subjects/{subject_id}`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `deactivate_subject`

```python
deactivate_subject(subject_id: str, idempotency_key: str | None, correlation_id: str | None) -> m.DesactivationSujet
```

Desactive un sujet (jamais d'effacement).

**Route :** `DELETE /subjects/{subject_id}`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `patch_subject_attributes`

```python
patch_subject_attributes(subject_id: str, attributs: dict[str, str], motif: str | None, fin_a: str | None, idempotency_key: str | None, correlation_id: str | None) -> m.Sujet
```

Ajuste les attributs (derogations) d'un sujet.

**Route :** `PATCH /subjects/{subject_id}/attributes`, `GET /subjects/{subject_id}/quotas`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `get_subject_quotas`

```python
get_subject_quotas(subject_id: str, correlation_id: str | None) -> m.Quotas
```

Quotas d'un sujet.

**Route :** `GET /subjects/{subject_id}/quotas`, `GET /subjects/{subject_id}/roles`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `get_subject_roles`

```python
get_subject_roles(subject_id: str, correlation_id: str | None) -> m.RolesSujet
```

Roles portes par un sujet.

**Route :** `GET /subjects/{subject_id}/roles`, `PUT /subjects/{subject_id}/roles`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `set_subject_roles`

```python
set_subject_roles(subject_id: str, roles: list[m.RoleAttribue | dict[str, Any]], motif: str | None, idempotency_key: str | None, correlation_id: str | None) -> m.Sujet
```

Remplace les roles d'un sujet.

**Route :** `PUT /subjects/{subject_id}/roles`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `list_audit`

```python
list_audit(curseur: str | None, taille: int | None, correlation_id: str | None) -> m.PageAudit
```

Journal d'audit IAM.

**Route :** `GET /audit`, `GET /projects`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.
