# Cellule reseau (agent)

`client.network` parle a **agent_reseau** (`gandal_agent`), pas a iaas-api.

!!! warning
    Pour lister / gerer les VM **metier** (projets, droits), utiliser
    `client.orchestration.vms` et `client.orchestration.networks`.
    La cellule sert aux operations techniques (XCP-ng, USER/ACL, IPAM, pfSense…).

## Prefrequis

- Agent joignable (souvent `http://127.0.0.1:8444`)
- Jeton = contenu de `.secrets/api-token` de l'agent
- Variables : `GANDAL_NETWORK_ENDPOINT`, `GANDAL_NETWORK_TOKEN`

```ini
# ~/.gandal/credentials
[default]
endpoint = http://localhost:8000
network_endpoint = http://127.0.0.1:8444
network_token = ...
```

## Contrat d'appel

Chaque action metier est un `POST /v1/<domaine>` avec :

```json
{
  "schema_version": 1,
  "target_id": "cluster-lab",
  "mode": "check",
  "action": "create_internal",
  "spec": { }
}
```

- **`check` avant `apply`** (toujours)
- Pas besoin d'`Idempotency-Key` (ignoree par l'agent)
- Reponse = enveloppe `NetworkExecution` (`execution_id`, `state`, `result`, `replay`)

## Exemples

```python
from gandal_sdk import GandalClient
from gandal_sdk.cells.network import NetworkMode

client = GandalClient.from_env()

print(client.network.health())

# Plan puis application (XCP-ng)
plan = client.network.create_network(
    target_id="cluster-lab",
    resource_key="request-a",
    name="Projet A",
    mode=NetworkMode.CHECK,
)
client.network.require_succeeded(plan)

done = client.network.create_network(
    target_id="cluster-lab",
    resource_key="request-a",
    name="Projet A",
    mode=NetworkMode.APPLY,
)
client.network.require_succeeded(done)

# Architecture ACL (reseau USER)
client.network.user_vms(
    "deploy",
    {
        "user_uuid": "...",
        "project_uuid": "...",
        "project_name": "boutique",
        "vm_uuid": "...",
    },
    target_id="cluster-prod",
    mode=NetworkMode.APPLY,
)

# Toute action documentee dans docs/endpoints de l'agent
client.network.run(
    "flows",
    "list",
    {},
    target_id="cluster-prod",
    mode=NetworkMode.CHECK,
)
```

## Domaines couverts via raccourcis

| Methode | Domaine agent |
| --- | --- |
| `run` / `submit` / `get_execution` / `health` | socle |
| `create_network` / `rename_network` / `delete_network` | `xcpng.networks` |
| `attach_vm` / `detach_vm` | `vm-networks` (EVPN) |
| `user_vms` | `user-vms` (ACL) |
| `vm_acl` | `vm-acl` |
| `flows` | `flows` |
| `xcpng(subdomain, …)` | `xcpng.*` |

`detach_vm_from_project` n'a **pas** d'equivalent unique : leve `GandalError` avec la marche a suivre.

Reference agent : depot `agent_reseau`, branche `refactor/decouple-overlay`, dossier `docs/endpoints/`.
