# B - Decisions

Autorisation simple et batch, catalogue d'actions.

**Acces :** `client.iam`

!!! note
    Sans endpoint IAM configure, chaque appel leve `CellUnavailable`. Les ecritures envoient une `Idempotency-Key` (sauf `create_access_key` et `assume_role`). Erreurs en `application/problem+json` → `GandalApiError`.

## `decide`

```python
decide(demande: m.DemandeDecision | dict[str, Any], correlation_id: str | None) -> m.Decision
```

Demande une decision d'autorisation (POST /decisions).

**Route :** `POST /decisions`, `POST /decisions:batch`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `decide_batch`

```python
decide_batch(demandes: list[m.DemandeDecision | dict[str, Any]], correlation_id: str | None) -> m.DecisionsGroupees
```

Decisions groupees (POST /decisions:batch).

**Route :** `POST /decisions:batch`, `GET /actions`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `list_actions`

```python
list_actions(correlation_id: str | None) -> m.CatalogueActions
```

Catalogue des actions connues du moteur de decision.

**Route :** `GET /actions`, `GET /subjects`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.
