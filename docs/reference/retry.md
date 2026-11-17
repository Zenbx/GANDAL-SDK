# RetryPolicy

```python
from gandal_sdk import RetryPolicy

RetryPolicy(max_attempts: int = 3, base_delay: float = 0.5, max_delay: float = 20.0)
```

- Respecte `Retry-After` si present
- Sinon attente exponentielle avec gigue
- Methodes idempotentes : GET, HEAD, OPTIONS, PUT, DELETE
- POST sans cle d'idempotence : pas de relance sur 503

Passe au constructeur : `GandalClient(..., retry=RetryPolicy(...))`.
