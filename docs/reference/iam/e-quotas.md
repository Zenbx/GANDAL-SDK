# E - Quotas et reservations

Quotas, propositions, reservations, resize.

**Acces :** `client.iam`

!!! note
    Sans endpoint IAM configure, chaque appel leve `CellUnavailable`. Les ecritures envoient une `Idempotency-Key` (sauf `create_access_key` et `assume_role`). Erreurs en `application/problem+json` → `GandalApiError`.

## `get_my_quotas`

```python
get_my_quotas(correlation_id: str | None) -> m.Quotas
```

Quotas de l'appelant.

**Route :** `GET /quotas`, `GET /quota-aggregates`, `POST /quota-capacity`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `get_quota_aggregates`

```python
get_quota_aggregates(correlation_id: str | None) -> m.Agregats
```

Agregats d'engagement de quotas (vue plateforme).

**Route :** `GET /quota-aggregates`, `POST /quota-capacity`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `publish_quota_capacity`

```python
publish_quota_capacity(mesures: dict[str, Any] | list[Any], mesure_le: str | None, idempotency_key: str | None, correlation_id: str | None) -> m.CapacitePubliee
```

Publie la capacite physique mesuree par la plateforme.

**Route :** `POST /quota-capacity`, `GET /quota-proposals`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `list_quota_proposals`

```python
list_quota_proposals(correlation_id: str | None) -> m.PagePropositions
```

Propositions de modification de plan.

**Route :** `GET /quota-proposals`, `POST /quota-proposals`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `propose_quota_plan`

```python
propose_quota_plan(plan: str, changements: dict[str, int], justification: str, effet_a: str | None, idempotency_key: str | None, correlation_id: str | None) -> m.Proposition
```

Propose une modification de plan de quotas.

**Route :** `POST /quota-proposals`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `decide_quota_proposal`

```python
decide_quota_proposal(proposal_id: str, verdict: str, motif: str | None, idempotency_key: str | None, correlation_id: str | None) -> m.DecisionProposition
```

Decide sur une proposition de plan.

**Route :** `POST /quota-proposals/{proposal_id}/decide`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `reserve_quota`

```python
reserve_quota(ressources: dict[str, int], projet: str | None, duree_s: int | None, ressource_portee: str | None, sujet_delegue: str | None, idempotency_key: str | None, correlation_id: str | None) -> m.Reservation
```

Reserve du quota avant creation de ressource.

**Route :** `POST /quota-reservations`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `get_reservation`

```python
get_reservation(reservation_id: str, correlation_id: str | None) -> m.Reservation
```

Lit une reservation de quota.

**Route :** `GET /quota-reservations/{reservation_id}`, `DELETE /quota-reservations/{reservation_id}`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `release_reservation`

```python
release_reservation(reservation_id: str, correlation_id: str | None) -> None
```

Libere une reservation non confirmee.

**Route :** `DELETE /quota-reservations/{reservation_id}`, `POST /quota-reservations/{reservation_id}/commit`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `commit_reservation`

```python
commit_reservation(reservation_id: str, ressource_id: str, ressource_type: str | None, idempotency_key: str | None, correlation_id: str | None) -> m.Reservation
```

Confirme une reservation apres creation effective.

**Route :** `POST /quota-reservations/{reservation_id}/commit`, `POST /resources/{resource_id}/release`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `release_resource`

```python
release_resource(resource_id: str, idempotency_key: str | None, correlation_id: str | None) -> m.Quotas
```

Libere le quota d'une ressource detruite.

**Route :** `POST /resources/{resource_id}/release`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `resize_resource`

```python
resize_resource(resource_id: str, quantites: dict[str, int], idempotency_key: str | None, correlation_id: str | None) -> m.Quotas
```

Redimensionne une ressource comptee (POST /resources/{id}/resize). Les quantites sont ABSOLUES, pas un ecart : c'est IAM qui soustrait, dans sa transaction. Les cles absentes restent inchangees. Seules les

**Route :** `POST /resources/{resource_id}/resize`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.
