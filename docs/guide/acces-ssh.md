# Acces SSH

`AccesSsh` demande un **certificat ephemere** au signeur, ouvre la session, puis detruit la cle.

## Python

```python
from gandal_sdk.acces_ssh import AccesSsh

with AccesSsh(jeton, signeur="https://10.30.0.30:8443") as a:
    a.entrer("poste-vision-01")
```

## CLI

```bash
export GANDAL_JETON=...
export GANDAL_SIGNEUR=https://10.30.0.30:8443
gandal-ssh poste-vision-01
```

## Variables

| Variable | Role |
| --- | --- |
| `GANDAL_JETON` | Jeton presente au signeur |
| `GANDAL_SIGNEUR` | URL de base du signeur |
| `GANDAL_CA` | CA TLS optionnel |

!!! note
    `GANDAL_JETON` n'est pas `GANDAL_TOKEN` (orchestration).

Voir [reference AccesSsh](../reference/acces-ssh.md) et la recette [Entrer dans une VM](../recettes/entrer-dans-une-vm.md).
