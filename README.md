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

## Identifiants, pagination et relances

**Identifiants.** `GandalClient.from_env()` trouve l'endpoint et le jeton sans
les ecrire dans le code, dans cet ordre : arguments, variables
`GANDAL_ENDPOINT` / `GANDAL_TOKEN`, puis profil de `~/.gandal/credentials`
(`GANDAL_PROFILE` pour en choisir un autre que `default`).

```ini
# ~/.gandal/credentials  (chmod 600)
[default]
endpoint = http://localhost:8000
token = eyJhbGciOi...
```

```python
client = GandalClient.from_env()              # profil default
admin = GandalClient.from_env(profile="admin")
```

**Pagination.** `paginate` parcourt toutes les pages de n'importe quelle methode
de liste, en chargeant les pages au fur et a mesure :

```python
from gandal_sdk import paginate

for vm in paginate(client.orchestration.vms.list, project_id, state="running"):
    print(vm.name)
```

**Relances.** Les `429`, et pour les requetes rejouables les `503` et erreurs
reseau, sont relances automatiquement (3 tentatives, attente exponentielle,
`Retry-After` respecte). Un `POST` n'est jamais rejoue sur `503` sans cle
d'idempotence, pour ne pas creer de doublon. Reglage :

```python
from gandal_sdk import RetryPolicy

client = GandalClient("http://localhost:8000", retry=RetryPolicy(max_attempts=5))
client = GandalClient("http://localhost:8000", retry=RetryPolicy(max_attempts=1))  # aucune relance
```

## Attendre qu'une ressource soit prete

Les actions sur l'infrastructure prennent du temps. Les waiters interrogent la
ressource jusqu'a l'etat voulu, et s'arretent tout de suite sur un etat dont
elle ne sortira pas seule (`error`, ou `deleting` quand on attend `running`) :

```python
from gandal_sdk import WaiterFailure, WaiterTimeout

request = client.orchestration.vms.request_create(project_id, VMCreateRequestIn(name="web-01", pack_id="pack-standard"))
try:
    accepted = client.orchestration.requests.wait_until_accepted(request.id)
    vm = client.orchestration.vms.wait_until_running(project_id, accepted.target_resource_id)
except WaiterFailure as err:      # refusee, annulee, VM en erreur...
    print(err, err.last_value)
except WaiterTimeout:
    ...
```

| Waiter | Succes | Echec immediat | Defaut |
| --- | --- | --- | --- |
| `vms.wait_until_running` / `wait_until_stopped` | etat atteint | `error`, `deleting` | 5 s x 60 |
| `vms.wait_until_deleted` | `404` | `error` | 5 s x 60 |
| `storages.wait_until_deleted` | `404` | - | 5 s x 60 |
| `requests.wait_until_accepted` | `accepted` | `refused`, `cancelled` | 15 s x 240 |

`unknown` n'est jamais traite comme un succes. Chaque waiter accepte `delay=`
et `max_attempts=`.

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

## Contrat avec l'API

Les regles communes aux services (erreurs, relances, idempotence, operations
longues, identifiants) sont dans [docs/CONVENTIONS_API.md](docs/CONVENTIONS_API.md).

`openapi/iaas-api.json` est un instantane de l'OpenAPI publiee par `iaas-api`.
`tests/test_contract_openapi.py` verifie que les modeles du SDK lisent et
envoient ce que l'API attend, et que chaque route publiee a son helper.
La CI compare chaque jour l'instantane a la branche `main` d'`iaas-api`.

Quand l'API change :

```bash
python scripts/sync_openapi.py --app-dir ../iaas-api   # ou --url http://localhost:8000
pytest tests/test_contract_openapi.py
```
