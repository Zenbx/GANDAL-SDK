# Erreurs et relances

## Hierarchie

| Exception | Sens |
| --- | --- |
| `GandalError` | Base SDK |
| `GandalApiError` | Erreur HTTP metier (`code`, `message`, `details`, `status`) |
| `CellUnavailable` | Cellule non configuree / stub |
| `DecisionRefusee` | IAM a repondu deny (`GardeIam`) |
| `AccesRefuse` / `SigneurIndisponible` | SSH refuse ou signeur down |
| `WaiterTimeout` / `WaiterFailure` | Attente d'etat |

## Orchestration

Format attendu :

```json
{ "error": { "code": "forbidden", "message": "...", "details": null } }
```

Si l'enveloppe manque, le SDK deduit `code` du statut HTTP (`unauthorized`, `not_found`, ...).

## IAM

Reponses `application/problem+json` (RFC 9457) mappees en `GandalApiError`
(`code` = dernier segment de `type`).

## Relances

```python
from gandal_sdk import GandalClient, RetryPolicy

client = GandalClient("http://localhost:8000", retry=RetryPolicy(max_attempts=5))
client = GandalClient("http://localhost:8000", retry=RetryPolicy(max_attempts=1))  # off
```

Relances sur `429`, et pour les methodes rejouables sur `503` / erreur reseau.
Un `POST` **sans** `Idempotency-Key` n'est jamais rejoue sur `503`.

Voir [Retry](../reference/retry.md) et [Erreurs](../reference/erreurs.md).
