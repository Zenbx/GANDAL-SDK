# Pagination et waiters

## Pagination

```python
from gandal_sdk import paginate

for vm in paginate(client.orchestration.vms.list, project_id, state="running"):
    print(vm.name)
```

`paginate` charge les pages a la demande (`page_size` defaut 100).
**IAM** utilise un curseur (`curseur` / `taille`) : pas de helper `paginate` IAM.

## Waiters orchestration

| Waiter | Succes | Echec immediat | Defaut |
| --- | --- | --- | --- |
| `vms.wait_until_running` / `stopped` | etat atteint | `error`, `deleting` | 5 s x 60 |
| `vms.wait_until_deleted` | 404 | `error` | 5 s x 60 |
| `storages.wait_until_deleted` | 404 | - | 5 s x 60 |
| `requests.wait_until_accepted` | `accepted` | `refused`, `cancelled` | 15 s x 240 |

```python
from gandal_sdk import WaiterFailure, WaiterTimeout

try:
    accepted = client.orchestration.requests.wait_until_accepted(request_id)
except WaiterFailure as err:
    print(err, err.last_value)
except WaiterTimeout:
    ...
```

Chaque waiter accepte `delay=` et `max_attempts=`.
