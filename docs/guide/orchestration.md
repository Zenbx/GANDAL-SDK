# Orchestration

Helpers typés sous `client.orchestration.*` pour `/api/v1`.

## Sous-clients

| Acces | Role |
| --- | --- |
| `auth` | login, me, mot de passe, suppression compte |
| `health` | `check` + `ready` |
| `projects` | projets, membres, invitations emises |
| `invitations` | invitations recues |
| `vms` | demandes create/update, power, console, share, delete |
| `storages` | demandes create/update, share, delete |
| `networks` | CRUD, attach/detach VM |
| `packs` | catalogue + admin |
| `requests` | liste, accept, refuse, cancel, waiter |
| `shares` | liste, revoke |
| `profiles` | droits, profils admin |

## Creation et modification = demandes

```python
from gandal_sdk.orchestration import VMCreateRequestIn

req = client.orchestration.vms.request_create(
    project_id,
    VMCreateRequestIn(name="web-01", pack_id="pack-standard"),
)
# req.id est une chaine UUID
accepted = client.orchestration.requests.wait_until_accepted(req.id)
```

!!! warning
    `RequestOut.id` et `ProfileOut.id` sont des **chaines**, pas des entiers.

## Suppression en deux temps

```python
preview = client.orchestration.vms.delete(project_id, vm_id)  # apercu
client.orchestration.vms.delete(project_id, vm_id, confirm=True)
```

## Pieges

- Helpers `storages` : certaines routes ont ete retirees cote backend → **404** possible.
- `auth.register` / `profiles.create_admin` : helpers conserves, routes absentes de l'OpenAPI actuel → **404**.
- Acces generique : `client.orchestration.get/post/put/patch/delete` sous `/api/v1`.
