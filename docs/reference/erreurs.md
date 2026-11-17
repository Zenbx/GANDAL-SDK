# Erreurs

Module `gandal_sdk.errors` (+ exceptions metier dans `garde` / `acces_ssh` / `waiters`).

## `GandalError`

Base de toutes les erreurs SDK.

## `GandalApiError`

```python
GandalApiError(code: str, message: str, *, details=None, status: int | None = None)
```

Attributs : `code`, `message`, `details`, `status`.

## `CellUnavailable`

```python
CellUnavailable(cell_name: str)
```

Cellule non branchee ou endpoint absent.

## Autres

- `DecisionRefusee` - voir [GardeIam](garde.md)
- `AccesRefuse`, `SigneurIndisponible` - voir [AccesSsh](acces-ssh.md)
- `WaiterError`, `WaiterTimeout`, `WaiterFailure` - voir [Waiters](waiters.md)
