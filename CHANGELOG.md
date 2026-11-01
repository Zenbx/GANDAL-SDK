# Journal des modifications

Format inspiré de [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/),
versions selon [SemVer](https://semver.org/lang/fr/). Le détail de chaque
version, migration comprise, est dans `docs/releases/`.

## [Non publié]

### Ajouté

- `client.hypervisor` fonctionnel avec la cellule gandal-hypervisor : création,
  modification, alimentation, suppression des VM du pool XCP-ng, opérations
  (`wait_for_operation`), waiters (`wait_until_running/stopped/deleted`), `health()`.
- `GandalClient(cell_urls=…, cell_tokens=…)` ; `from_env()` lit
  `GANDAL_HYPERVISOR_ENDPOINT` / `GANDAL_HYPERVISOR_TOKEN` et les clés de profil
  `hypervisor_endpoint` / `hypervisor_token`.
- Instantané `openapi/gandal-hypervisor.json`, test de contrat de la cellule,
  `scripts/run_hypervisor_integration.sh` (faux pool ou pool réel).

### Modifié (incompatible)

- `HypervisorCell.create_vm` renvoie `CreatedVm` (VM + opération) au lieu de
  `VmRef` ; `update_vm`, `power` et `delete_vm` renvoient une `CellOperation`.
  Ces méthodes levaient toutes `CellUnavailable` jusqu'ici.

## [0.3.0] - 2026-11-01

Notes complètes : [docs/releases/v0.3.0.md](docs/releases/v0.3.0.md).

### Modifié (incompatible)

- `ProfileOut.id`, `RequestOut.id` et tous les `profile_id` sont des entiers,
  comme dans l'API ; `profiles.update/delete` et `requests.get/cancel/accept/refuse`
  prennent un `int`.
- Sans enveloppe `{error: …}`, `GandalApiError.code` est déduit du statut HTTP
  (`unauthorized`, `not_found`…) au lieu de `internal_error`, et `message`
  reprend `detail`.
- Les requêtes sont relancées automatiquement (3 tentatives) sur `429`, et pour
  les requêtes rejouables sur `503` et erreur réseau.

### Ajouté

- `GandalClient.from_env()` et `gandal_sdk.credentials` : endpoint et jeton depuis
  les arguments, `GANDAL_ENDPOINT` / `GANDAL_TOKEN`, ou `~/.gandal/credentials`.
- `RetryPolicy` et le paramètre `retry=` de `GandalClient`.
- `paginate()` pour parcourir toutes les pages de n'importe quelle liste.
- Waiters : `vms.wait_until_running/stopped/deleted`,
  `storages.wait_until_deleted`, `requests.wait_until_accepted`, et les
  exceptions `WaiterError`, `WaiterFailure`, `WaiterTimeout`.
- Marqueur `py.typed` : les annotations du SDK sont utilisables par mypy et les
  éditeurs.
- `docs/CONVENTIONS_API.md`, instantané `openapi/iaas-api.json` et
  `scripts/sync_openapi.py`.
- Tests de contrat OpenAPI, tests d'intégration contre une vraie iaas-api
  (`scripts/run_integration.sh`), tests de relance sur de vraies sockets.
- CI : Python 3.11 à 3.13, intégration, wheel installé, dérive OpenAPI quotidienne,
  actions GitHub en versions Node 24.

### Corrigé

- `profiles.list()` et toute lecture de profil ou de demande échouaient contre
  la vraie API (identifiants entiers refusés par la validation).
- `wait_until_deleted` ne reconnaissait pas le `404` renvoyé par l'API actuelle.
- Déclaration de licence au format SPDX (l'ancien format cessera d'être accepté
  par setuptools en février 2027).

## [0.2.0] - 2026-10-31

### Ajouté

- Helpers typés pour toute la surface `/api/v1` décrite dans `API_ENDPOINTS.md` :
  projets, membres, invitations, VMs, stockages, réseaux, partages, packs,
  demandes, profils, authentification.

## [0.1.0] - 2026-10-31

### Ajouté

- Squelette du SDK : `GandalClient`, transport HTTP, `GandalApiError`, stubs des
  cellules IAM, hyperviseur, réseau, stockage, DNS et notifications.

[0.3.0]: https://github.com/Zenbx/GANDAL-SDK/compare/e4d93b9...v0.3.0
[0.2.0]: https://github.com/Zenbx/GANDAL-SDK/commit/e4d93b9
[0.1.0]: https://github.com/Zenbx/GANDAL-SDK/commit/059e98a
