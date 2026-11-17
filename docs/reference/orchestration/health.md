# Health (orchestration)

Sondes de sante. `ready()` n'est pas sous `/api/v1`.

**Acces :** `client.orchestration.health`

!!! tip
    `OrchestrationApi.health()` appelle `check()`. Pour `ready()`, utiliser `client.orchestration.health.ready()`.

## `check`

```python
check() -> HealthOut
```

Appelle GET /api/v1/health : le processus repond-il ?

**Route :** `GET /api/v1/health`, `GET /ready`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `ready`

```python
ready() -> ReadinessOut
```

Appelle GET /ready : l'API peut-elle SERVIR ? `check` dit que le processus repond ; `ready` qu'il a ses dependances. C'est `ready` que vise une sonde d'orchestrateur avant d'envoyer du

**Route :** `GET /ready`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.
