# GANDAL SDK

SDK Python pour les **apps externes** de la plateforme GANDAL.

Il expose un client unique (`GandalClient`) qui parle :

- a l'API d'orchestration (`/api/v1`) des maintenant ;
- aux services des autres cellules (IAM, hyperviseur, reseau, stockage, DNS, notifications) au fur et a mesure qu'ils sont livres.

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

client = GandalClient(base_url="http://localhost:8000")
client.login("alice@iaas.cm", "alice123")

print(client.orchestration.health())
me = client.orchestration.auth.me()
print(me.email)
```

## Feuille de route des cellules

| Module | Statut |
| --- | --- |
| `client.orchestration` | Disponible (auth, health, requetes generiques `/api/v1`) |
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
