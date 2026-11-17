# GandalClient

Point d'entree unique du SDK.

## Constructeur

```python
GandalClient(
    base_url: str,
    *,
    timeout: float = 30.0,
    retry: RetryPolicy | None = None,
    cell_urls: dict[str, str] | None = None,
    cell_tokens: dict[str, str] | None = None,
    cell_verify: dict[str, bool | str] | None = None,
)
```

Attributs : `orchestration`, `iam`, `hypervisor`, `network`, `storage`, `dns`, `notifications`.

## `from_env`

```python
GandalClient.from_env(
    *,
    endpoint: str | None = None,
    token: str | None = None,
    profile: str | None = None,
    timeout: float = 30.0,
    retry: RetryPolicy | None = None,
) -> GandalClient
```

Branche automatiquement hypervisor / IAM depuis credentials.

## Methodes

| Methode | Role |
| --- | --- |
| `login(email, password)` | Auth orchestration + pose le Bearer |
| `me()` | Identite courante |
| `set_token(token)` | Bearer orchestration |
| `set_iam_token(token)` | Bearer IAM |
| `close()` | Ferme les transports |
| context manager | `with GandalClient(...) as c:` |

**Exceptions :** `GandalError` si endpoint manquant dans `from_env` ; `CellUnavailable` sur `set_iam_token` sans endpoint IAM.
