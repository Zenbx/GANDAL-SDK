# Identifiants

Resolution via `gandal_sdk.credentials.resolve_credentials`, utilisee par `GandalClient.from_env()`.

## Ordre de priorite (champ par champ)

1. Arguments explicites (`endpoint=`, `token=`, `profile=`)
2. Variables d'environnement
3. Fichier `~/.gandal/credentials` (ou `GANDAL_CREDENTIALS_FILE`)

## Fichier credentials

```ini
# ~/.gandal/credentials  (chmod 600)
[default]
endpoint = https://api.gandal.example
token = eyJhbGciOi...
hypervisor_endpoint = http://127.0.0.1:8770
hypervisor_token = ...
iam_endpoint = https://10.30.0.30:8081/v1
iam_token = ...
iam_ca = ~/.gandal/gandal-ca.crt
network_endpoint = http://127.0.0.1:8444
network_token = ...

[admin]
endpoint = https://api.gandal.example
token = eyJhbGciOi...
```

```python
from gandal_sdk import GandalClient

client = GandalClient.from_env()
admin = GandalClient.from_env(profile="admin")
```

## Variables d'environnement

| Variable | Role |
| --- | --- |
| `GANDAL_ENDPOINT` | URL iaas-api |
| `GANDAL_TOKEN` | Bearer orchestration |
| `GANDAL_PROFILE` | Section credentials |
| `GANDAL_CREDENTIALS_FILE` | Chemin alternatif du fichier |
| `GANDAL_HYPERVISOR_ENDPOINT` / `GANDAL_HYPERVISOR_TOKEN` | Cellule hyperviseur |
| `GANDAL_IAM_ENDPOINT` / `GANDAL_IAM_TOKEN` / `GANDAL_IAM_CA` | Cellule IAM (+ CA TLS) |
| `GANDAL_NETWORK_ENDPOINT` / `GANDAL_NETWORK_TOKEN` | Cellule reseau (agent) |
| `GANDAL_JETON` | Jeton pour `gandal-ssh` / `AccesSsh` |
| `GANDAL_SIGNEUR` | URL du signeur SSH |
| `GANDAL_CA` | CA pour le signeur SSH |

## Jetons par surface

```python
client.set_token(orch_jwt)           # uniquement orchestration
client.set_iam_token(iam_jwt)        # uniquement cellule IAM (endpoint requis)
client.set_network_token(net_token)  # uniquement agent reseau (endpoint requis)
```

Sans endpoint configure, `set_iam_token` / `set_network_token` levent `CellUnavailable`.
