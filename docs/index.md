# GANDAL SDK

SDK Python **0.7.0** pour les applications qui consomment la plateforme GANDAL.

Il expose un client unique (`GandalClient`) qui parle :

- a l'**API d'orchestration** (`iaas-api`, helpers typés `/api/v1`) ;
- a la cellule **IAM** (decision-service + OIDC) ;
- a la cellule **hyperviseur** (pool XCP-ng) ;
- aux autres cellules (reseau, stockage, DNS, notifications) quand elles seront livrees (stubs aujourd'hui).

Le SDK n'est pas un serveur : il s'installe dans votre app et appelle les services deja deployes.

## Par ou commencer

1. [Demarrage](guide/demarrage.md) - installation et premier login
2. [Architecture](guide/architecture.md) - orchestration vs cellules
3. [Creer une VM](recettes/creer-une-vm.md) - parcours bout en bout
4. [Reference client](reference/client.md) - surface publique

## Lire cette doc en local

```bash
pip install -e ".[dev]"
mkdocs serve
```

Puis ouvrir l'URL affichee (souvent `http://127.0.0.1:8000`).

## Installation du paquet

```bash
pip install "git+https://github.com/Zenbx/GANDAL-SDK.git@v0.7.0"
```

## Versions

Notes de release : [v0.7.0](releases/v0.7.0.md). Journal : voir `CHANGELOG.md` a la racine du depot.
