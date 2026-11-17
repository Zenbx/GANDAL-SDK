# G - Ressources et tags

Metadonnees de ressources comptees et tags.

**Acces :** `client.iam`

!!! note
    Sans endpoint IAM configure, chaque appel leve `CellUnavailable`. Les ecritures envoient une `Idempotency-Key` (sauf `create_access_key` et `assume_role`). Erreurs en `application/problem+json` → `GandalApiError`.

## `get_resource`

```python
get_resource(resource_id: str, correlation_id: str | None) -> dict[str, Any]
```

Lit les metadonnees IAM d'une ressource.

**Route :** `GET /resources/{resource_id}`, `POST /resources/{resource_id}/grants`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `grant_resource_right`

```python
grant_resource_right(resource_id: str, droit: m.DroitEntree | dict[str, Any], idempotency_key: str | None, correlation_id: str | None) -> dict[str, Any]
```

Accorde un droit sur une ressource.

**Route :** `POST /resources/{resource_id}/grants`, `DELETE /resources/{resource_id}/grants/{cible_type}/{cible}`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `revoke_resource_right`

```python
revoke_resource_right(resource_id: str, cible_type: str, cible: str, idempotency_key: str | None, correlation_id: str | None) -> dict[str, Any]
```

Retire un droit sur une ressource.

**Route :** `DELETE /resources/{resource_id}/grants/{cible_type}/{cible}`, `GET /resources/{resource_id}/quotas`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `get_resource_quotas`

```python
get_resource_quotas(resource_id: str, correlation_id: str | None) -> dict[str, Any]
```

Quotas attaches a une ressource.

**Route :** `GET /resources/{resource_id}/quotas`, `GET /tags/{portee}/{cible}`, `PATCH /tags/{portee}/{cible}`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `get_tags`

```python
get_tags(portee: str, cible: str, correlation_id: str | None) -> dict[str, Any]
```

Lit les attributs (tags) d'une cible.

**Route :** `GET /tags/{portee}/{cible}`, `PATCH /tags/{portee}/{cible}`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `set_tags`

```python
set_tags(portee: str, cible: str, attributs: m.AttributsEntree | dict[str, Any], idempotency_key: str | None, correlation_id: str | None) -> dict[str, Any]
```

Pose les attributs (tags) d'une cible.

**Route :** `PATCH /tags/{portee}/{cible}`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.
