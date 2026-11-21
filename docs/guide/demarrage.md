# Demarrage

## Prerequisites

- Python **>= 3.11**
- Acces a une instance **iaas-api** (orchestration)
- Optionnel : endpoints IAM et hyperviseur pour les cellules

## Installer le SDK

=== "Depuis le tag"

    ```bash
    pip install "git+https://github.com/Zenbx/GANDAL-SDK.git@v0.7.0"
    ```

=== "Editable (contribution)"

    ```bash
    git clone https://github.com/Zenbx/GANDAL-SDK.git
    cd GANDAL-SDK
    pip install -e ".[dev]"
    ```

## Premier client

```python
from gandal_sdk import GandalClient

with GandalClient("http://localhost:8000") as client:
    client.login("alice@iaas.cm", "alice123")
    me = client.me()
    print(me.email, me.role)

    projects = client.orchestration.projects.list()
    for project in projects.items:
        print(project.id, project.name)
```

## Sans mot de passe dans le code

Preferer `from_env()` et un fichier d'identifiants (voir [Identifiants](identifiants.md)) :

```python
from gandal_sdk import GandalClient

client = GandalClient.from_env()  # GANDAL_ENDPOINT + GANDAL_TOKEN ou ~/.gandal/credentials
print(client.me().email)
```

## Verifier que l'API repond

```python
print(client.orchestration.health().status)           # processus vivant
print(client.orchestration.health.ready().status)     # pret a servir (GET /ready)
```

!!! tip
    `health()` sur la facade appelle `check()` (`GET /api/v1/health`).
    Pour la sonde d'orchestrateur, utilisez `client.orchestration.health.ready()`.

## Suite

- [Architecture](architecture.md)
- [Orchestration](orchestration.md)
- Recette [Creer une VM](../recettes/creer-une-vm.md)
