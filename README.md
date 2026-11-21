# GANDAL SDK

SDK Python pour les **apps externes** de la plateforme GANDAL (version **0.7.0**).

Il expose un client unique (`GandalClient`) qui parle :

- a l'API d'**orchestration** (`iaas-api`, helpers typés `/api/v1`) ;
- a la cellule **IAM** (decision-service + OIDC) ;
- a la cellule **hyperviseur** (pool XCP-ng) ;
- a la cellule **reseau** (`agent_reseau`, executions `/v1`) ;
- aux cellules restantes (stockage, DNS, notifications) au fur et a mesure
  qu'elles sont livrees (stubs pour l'instant).

Le SDK n'est **pas** un serveur : vous l'installez dans votre application, qui
appelle ensuite les services GANDAL deja deployes.

| Vous voulez… | Allez a |
| --- | --- |
| Utiliser le SDK dans une app | [Installer le SDK (utilisateur)](#installer-le-sdk-utilisateur) |
| Contribuer / developper le depot | [Developper sur le SDK](#developper-sur-le-sdk) |
| Lire la doc complete | [Documentation](#documentation) |

---

## Prerequisites

- **Python 3.11 ou plus** (`python --version`)
- **pip** (`python -m pip --version`)
- Pour installer depuis Git : **Git** dans le `PATH` (`git --version`)
- Pour appeler l'API : une instance **iaas-api** joignable (et optionnellement IAM / hyperviseur)

Sous **Windows (PowerShell)**, mettez toujours les URL et extras entre guillemets :
sans eux, `@v0.7.0` et `.[dev]` peuvent etre mal interpretes.

---

## Installer le SDK (utilisateur)

Choisissez **une** des methodes. Puis passez a [Verifier l'installation](#verifier-linstallation).

### Methode A - depuis le tag Git (recommandee)

Necessite Git.

```bash
python -m pip install "git+https://github.com/Zenbx/GANDAL-SDK.git@v0.7.0"
```

PowerShell (identique, guillemets obligatoires) :

```powershell
python -m pip install "git+https://github.com/Zenbx/GANDAL-SDK.git@v0.7.0"
```

### Methode B - wheel de la release (sans Git)

Utile si Git n'est pas installe, ou pour un CI minimal :

```bash
python -m pip install "https://github.com/Zenbx/GANDAL-SDK/releases/download/v0.7.0/gandal_sdk-0.7.0-py3-none-any.whl"
```

### Methode C - branche `main` (dernier code, non fige)

```bash
python -m pip install "git+https://github.com/Zenbx/GANDAL-SDK.git"
```

### Verifier l'installation

```bash
python -c "import gandal_sdk; print(gandal_sdk.__version__)"
```

Attendu : `0.7.0` (ou la version du tag / de `main` installee).

La commande CLI SSH est aussi disponible apres install :

```bash
gandal-ssh --help
```

---

## Premier usage

### Client minimal (login)

```python
from gandal_sdk import GandalClient
from gandal_sdk.orchestration import VMCreateRequestIn, PowerAction

with GandalClient("http://localhost:8000") as client:
    client.login("alice@iaas.cm", "alice123")
    print(client.me().email)
    print(client.orchestration.health().status)

    projects = client.orchestration.projects.list()
    project_id = projects.items[0].id

    vms = client.orchestration.vms.list(project_id)
    if vms.items:
        print(vms.items[0].name, vms.total_items)

    # Creation = demande admin (pas un create direct)
    client.orchestration.vms.request_create(
        project_id,
        VMCreateRequestIn(name="web-01", pack_id="pack-standard"),
    )
```

### Identifiants hors du code (`from_env`)

Ordre de resolution : arguments → variables d'environnement → fichier profil.

```ini
# ~/.gandal/credentials   (Linux/macOS : chmod 600)
# Windows : %USERPROFILE%\.gandal\credentials
[default]
endpoint = http://localhost:8000
token = eyJhbGciOi...
hypervisor_endpoint = http://127.0.0.1:8770
hypervisor_token = ...
iam_endpoint = https://10.30.0.30:8081/v1
iam_token = ...
iam_ca = ~/.gandal/gandal-ca.crt
network_endpoint = http://127.0.0.1:8444
network_token = ...
```

Variables equivalentes : `GANDAL_ENDPOINT`, `GANDAL_TOKEN`, `GANDAL_PROFILE`,
`GANDAL_HYPERVISOR_*`, `GANDAL_IAM_*`, `GANDAL_NETWORK_*`
(detail dans la [doc Identifiants](docs/guide/identifiants.md)).

```python
from gandal_sdk import GandalClient

client = GandalClient.from_env()
admin = GandalClient.from_env(profile="admin")
```

### Pagination, waiters, relances

```python
from gandal_sdk import paginate, RetryPolicy, WaiterFailure, WaiterTimeout

for vm in paginate(client.orchestration.vms.list, project_id, state="running"):
    print(vm.name)

client = GandalClient("http://localhost:8000", retry=RetryPolicy(max_attempts=5))

request = client.orchestration.vms.request_create(
    project_id, VMCreateRequestIn(name="web-01", pack_id="pack-standard")
)
try:
    accepted = client.orchestration.requests.wait_until_accepted(request.id)
    vm = client.orchestration.vms.wait_until_running(
        project_id, accepted.target_resource_id
    )
except WaiterFailure as err:
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

### Cellules IAM, hyperviseur et reseau (apercu)

Sans endpoint configure, `client.iam` / `client.hypervisor` / `client.network`
levent `CellUnavailable`.

```python
# IAM : GANDAL_IAM_ENDPOINT / TOKEN / CA, ou cell_urls / cell_tokens / cell_verify
from gandal_sdk.cells.iam import DemandeDecision, DemandeRessource

decision = client.iam.decide(
    DemandeDecision(
        action="vm:create",
        ressource=DemandeRessource(type="vm", projet="prj_01"),
        contexte={"ram_gb": 2},
    )
)

# Hyperviseur : GANDAL_HYPERVISOR_ENDPOINT / TOKEN
from gandal_sdk.cells.hypervisor import PowerAction, VmSpec

created = client.hypervisor.create_vm(
    VmSpec(name="sdk-it-web", ram_gb=1, vcpu=1, vram_gb=0, ssd_gb=10)
)
client.hypervisor.wait_for_operation(created.operation)

# Reseau : GANDAL_NETWORK_ENDPOINT / TOKEN (toujours check puis apply)
from gandal_sdk.cells.network import NetworkMode

plan = client.network.create_network(
    target_id="cluster-lab",
    resource_key="request-a",
    name="Projet A",
    mode=NetworkMode.CHECK,
)
client.network.require_succeeded(plan)
```

Guides detailles : [Garde IAM](docs/guide/garde-iam.md), [Acces SSH](docs/guide/acces-ssh.md),
[Hyperviseur](docs/guide/hyperviseur.md), [Reseau](docs/guide/reseau.md),
recettes sous [docs/recettes/](docs/recettes/).

---

## Developper sur le SDK

Pour modifier le code, lancer les tests, regenerer la doc ou synchroniser OpenAPI.

### 1. Cloner et environnement

```bash
git clone https://github.com/Zenbx/GANDAL-SDK.git
cd GANDAL-SDK
python -m venv .venv
```

Activer le venv :

```bash
# Linux / macOS
source .venv/bin/activate

# Windows PowerShell
.\.venv\Scripts\Activate.ps1
```

### 2. Installer en editable (+ outils de dev)

```bash
python -m pip install -U pip
python -m pip install -e ".[dev]"
```

L'extra `dev` tire : pytest, respx, ruff, **mkdocs** / mkdocs-material.

Verifier :

```bash
python -c "import gandal_sdk; print(gandal_sdk.__version__, gandal_sdk.__file__)"
ruff check src tests scripts
pytest -q
```

### 3. Lire / regenerer la documentation

```bash
mkdocs serve
```

Ouvrir l'URL affichee (souvent `http://127.0.0.1:8000`).

Build strict (CI locale) :

```bash
mkdocs build --strict
```

La reference methode-par-methode peut etre regeneree depuis le code :

```bash
python scripts/gen_reference_docs.py
```

### 4. Tests

```bash
# Unitaires (pas de reseau externe)
pytest -q

# Style
ruff check src tests scripts

# Integration contre une vraie iaas-api (clone voisin + deps API)
# Linux / macOS / Git Bash :
scripts/run_integration.sh ../iaas-api ../iaas-api/.venv/bin/python
```

Le script d'integration applique les migrations **Alembic** puis demarre iaas-api
sur une base SQLite neuve, lance `tests/integration`, puis arrete le serveur.

Integration hyperviseur :

```bash
scripts/run_hypervisor_integration.sh ../gandal-hypervisor
# Windows :
# $env:GANDAL_HV_FAKE='0'; $env:GANDAL_IT_SSD_GB='25'; $env:GANDAL_IT_DELAY='5'
# .\scripts\run_hypervisor_integration.ps1 ..\gandal-hypervisor
```

### 5. Contrat OpenAPI

Quand iaas-api (ou une cellule) change :

```bash
python scripts/sync_openapi.py --app-dir ../iaas-api
# IAM :
# python scripts/sync_openapi.py --service gandal-iam --yaml ../iam/iam/contracts/openapi-iam.yaml
pytest tests/test_contract_openapi.py
```

Conventions communes : [docs/CONVENTIONS_API.md](docs/CONVENTIONS_API.md).
Publication d'une version : [docs/RELEASING.md](docs/RELEASING.md).

---

## Surface disponible

### Orchestration (`client.orchestration`)

| Acces | Couverture |
| --- | --- |
| `auth` | login, me, update_me, change_password, delete_me |
| `projects` | CRUD, membres, invitations, suppression confirmee |
| `invitations` | liste / accept / refuse / cancel |
| `vms` | liste, get, demandes create/update, power, console, share, delete |
| `storages` | liste, get, demandes create/update, share, delete |
| `networks` | CRUD, attach/detach VM, delete |
| `packs` | catalogue + admin create/update/delete |
| `requests` | liste, get, cancel, accept, refuse, waiter |
| `shares` | liste, get, list_for_project, revoke |
| `profiles` | rights, profiles admin |

Methodes generiques `get` / `post` / `put` / `patch` / `delete` en echappatoire.

### Feuille de route des cellules

| Module | Statut |
| --- | --- |
| `client.orchestration` | Disponible (helpers typés `/api/v1`) |
| `client.iam` | Disponible ; contrat 1.7.0 (familles A-G) |
| `client.hypervisor` | Disponible ; valide faux pool et pool XCP-ng (bac a sable) |
| `client.network` | Disponible ; agent_reseau (executions `/v1`, check/apply) |
| `client.storage` | Stub |
| `client.dns` | Stub |
| `client.notifications` | Stub |

---

## Documentation

- Site MkDocs : `mkdocs serve` puis [docs/index.md](docs/index.md)
- Guides : [docs/guide/](docs/guide/)
- Recettes : [docs/recettes/](docs/recettes/)
- Reference : [docs/reference/](docs/reference/)
- Journal : [CHANGELOG.md](CHANGELOG.md)
- Releases : [docs/releases/](docs/releases/)

Depot : https://github.com/Zenbx/GANDAL-SDK  
Release courante : https://github.com/Zenbx/GANDAL-SDK/releases/tag/v0.7.0
