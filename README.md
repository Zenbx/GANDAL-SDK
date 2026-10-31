# GANDAL SDK

SDK Python pour les **apps externes** de la plateforme GANDAL.

Il expose un client unique (`GandalClient`) qui parle :

- a l'API d'orchestration (`/api/v1`) avec des **helpers typés** ;
- aux services des autres cellules (IAM, hyperviseur, reseau, stockage, DNS, notifications) au fur et a mesure qu'ils sont livres (stubs pour l'instant).

Le SDK n'est pas un serveur : il s'installe dans l'app cliente et appelle les services deja deployes.

## Installation

```bash
pip install -e ".[dev]"
```

Ou depuis le depot :

```bash
pip install git+https://github.com/Zenbx/GANDAL-SDK.git
```

## Usage rapide

```python
from gandal_sdk import GandalClient
from gandal_sdk.orchestration import VMCreateRequestIn, PowerAction

client = GandalClient(base_url="http://localhost:8000")
client.login("alice@iaas.cm", "alice123")

print(client.orchestration.health().status)

projects = client.orchestration.projects.list()
project_id = projects.items[0].id

vms = client.orchestration.vms.list(project_id)
print(vms.items[0].name, vms.total_items)

# Demande de creation (passe par un administrateur)
client.orchestration.vms.request_create(
    project_id,
    VMCreateRequestIn(name="web-01", pack_id="pack-standard"),
)

# Action directe d'alimentation
client.orchestration.vms.power(project_id, vms.items[0].id, PowerAction.START)

# Suppression en deux temps (confirm=True enchaine apercu + confirmation)
client.orchestration.vms.delete(project_id, vms.items[0].id, confirm=True)
```

## Helpers typés disponibles (orchestration)

| Acces | Couverture |
| --- | --- |
| `client.orchestration.auth` | login, me, update_me, change_password, delete_me |
| `client.orchestration.projects` | CRUD, membres, invitations de projet, suppression confirmee |
| `client.orchestration.invitations` | liste / accept / refuse / cancel |
| `client.orchestration.vms` | liste, get, demandes create/update, power, console, share, delete |
| `client.orchestration.storages` | liste, get, demandes create/update, share, delete |
| `client.orchestration.networks` | CRUD, attach/detach VM, delete |
| `client.orchestration.packs` | catalogue + admin create/update/delete |
| `client.orchestration.requests` | liste, get, cancel, accept, refuse |
| `client.orchestration.shares` | liste, get, list_for_project, revoke |
| `client.orchestration.profiles` | rights, profiles admin |

Les methodes generiques `get/post/put/patch/delete` restent disponibles en echappatoire.

## Feuille de route des cellules

| Module | Statut |
| --- | --- |
| `client.orchestration` | Disponible (helpers typés `/api/v1`) |
| `client.iam` | Stub - en attente de l'API cellule |
| `client.hypervisor` | Stub - en attente de l'API cellule |
| `client.network` | Stub - en attente de l'API cellule |
| `client.storage` | Stub - en attente de l'API cellule |
| `client.dns` | Stub - en attente de l'API cellule |
| `client.notifications` | Stub - en attente de l'API cellule |

## Developpement

```bash
pytest
```
