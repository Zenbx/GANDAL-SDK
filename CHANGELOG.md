# Journal des modifications

Format inspiré de [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/),
versions selon [SemVer](https://semver.org/lang/fr/). Le détail de chaque
version, migration comprise, est dans `docs/releases/`.

## [Non publié]

### Corrigé (incompatible)

- **`RequestOut.id` est une CHAINE**, plus un entier, et les cinq signatures
  `request_id` suivent. Le backend rend un UUID
  (`7bc3e3bb-fa40-417e-b4bc-3386008a8edf`) : déclaré `int`, ce champ faisait
  lever Pydantic à **chaque dépôt de demande** — le SDK était inutilisable sur
  `vms.request_create`, `vms.request_update` et tout `requests.*`. Aucun test de
  l'un ou l'autre côté ne pouvait le voir : ceux du SDK valident ses propres
  modèles, ceux du backend les siens.

### Corrigé — les divergences avec le backend, tranchées

Mesurées en faisant parler le vrai SDK au vrai backend
(`GANDAL-BACKEND-IaaS/iaas-api`, `f9aff99`), et corrigées du côté qui avait tort.

- **`ProfileOut.id` est une chaîne.** Le backend stocke les profils en
  `String(36)`, comme tout le reste du système : projets (`prj_…`), VM (`vm_…`),
  demandes et partages sont tous des UUID. Un entier séquentiel ici aurait été le
  seul identifiant devinable de la plateforme, et il révélerait combien de profils
  existent. Les paramètres `profile_id` suivent.
- **Les trois noms de schéma du test de contrat** suivent le backend :
  `ProfileCreate` → `ProfileCreateIn`, `ProfileUpdate` → `ProfileUpdateIn`,
  `PaginatedProfilesOut` → `Page_ProfileOut_`. À noter : les modèles du SDK
  s'appelaient **déjà** `ProfileCreateIn`/`ProfileUpdateIn` et utilisaient déjà
  `Page[ProfileOut]` — c'étaient les chaînes du test qui étaient restées sur
  l'ancienne version. Le SDK était cohérent ; seul son contrôle ne l'était plus.
- **`openapi/iaas-api.json` resynchronisé** : 6 routes → **46**.
- **`RegisterIn` et `ReadinessOut`** ajoutés, et trois modèles de plus entrent
  sous contrôle de contrat (`RegisterIn`, `ReadinessOut`, `RequestOut`).

### Ajouté — les trois routes qui n'avaient pas de helper

- `auth.register(body)` — `POST /api/v1/auth/register`. Le jeton est posé sur le
  transport, comme pour `login` : après une inscription, l'appelant est connecté.
  Ne pas le poser obligerait à enchaîner `register` puis `login`, et l'un des
  deux finirait par être oublié.
- `health.ready()` — `GET /ready`, et noter qu'elle n'est **pas** sous `/api/v1`.
  `check()` dit que le processus répond ; `ready()` qu'il peut **servir**. C'est
  `ready` que vise une sonde d'orchestrateur avant d'envoyer du trafic. Elle rend
  aussi le réglage du service de décision du backend (`off` | `fake` | `gandal`),
  ce qu'une supervision doit surveiller.
- `profiles.create_admin(body)` — `POST /api/v1/admin/admins`. Rend l'**identité**
  créée, pas un jeton : contrairement à `register`, celui qui crée
  l'administrateur n'est pas celui qui l'utilisera.

### Corrigé — le détecteur de couverture criait à tort

`tests/contract.py` déclarait les trois routes `.../deletion` « non couvertes »
alors que le SDK les appelle — via `delete_two_step`, dont la méthode n'est pas
littérale à côté du chemin. Le détecteur les lit maintenant. **Un contrôle qui
crie à tort finit par être ignoré en bloc, y compris le jour où il a raison.**

### À savoir — mesuré, et laissé en place

Le SDK garde cinq helpers `storages` (`projects/{id}/storages…`) pour des routes
que le backend a **retirées** (`978aeab Remove DNS and storage scope`). Ils
rendront 404. Ils ne sont pas supprimés ici : « retiré du périmètre » peut
vouloir dire « reporté », et détruire ce travail n'est pas une décision à prendre
seul. Le test de couverture ne voit pas ce sens-là — il vérifie qu'une route
publiée a un helper, pas qu'un helper a une route.

## [0.5.0] - 2026-11-04

Notes complètes : [docs/releases/v0.5.0.md](docs/releases/v0.5.0.md).

### Ajouté

- `client.iam` fonctionnel sur le contrat IAM 1.7.0 (70 routes) : décisions,
  sujets, projets, accès, quotas/réservations, machines/clés/STS, politiques,
  ressources/tags, OIDC/JWKS.
- `GANDAL_IAM_ENDPOINT` / `GANDAL_IAM_TOKEN` / `GANDAL_IAM_CA` et clés de profil
  `iam_endpoint` / `iam_token` / `iam_ca` ; `cell_verify` pour le CA TLS.
- Instantané `openapi/gandal-iam.json`, test de contrat, mapping RFC 9457
  (`application/problem+json`) dans le transport HTTP.
- `scripts/sync_openapi.py --service gandal-iam --yaml …`.

### Modifié (incompatible)

- L'ancien stub `IamCell` (`login`, `validate_token`, `get_rights`…) est remplacé
  par l'API alignée sur le contrat (ex. `decide`, `get_me`, `reserve_quota`).
  Sans endpoint IAM, les appels lèvent toujours `CellUnavailable`.

## [0.4.0] - 2026-11-02

Notes complètes : [docs/releases/v0.4.0.md](docs/releases/v0.4.0.md).

### Ajouté

- `client.hypervisor` fonctionnel avec la cellule gandal-hypervisor : création,
  modification, alimentation, suppression des VM du pool XCP-ng, opérations
  (`wait_for_operation`), waiters (`wait_until_running/stopped/deleted`), `health()`.
- `GandalClient(cell_urls=…, cell_tokens=…)` ; `from_env()` lit
  `GANDAL_HYPERVISOR_ENDPOINT` / `GANDAL_HYPERVISOR_TOKEN` et les clés de profil
  `hypervisor_endpoint` / `hypervisor_token`.
- Instantané `openapi/gandal-hypervisor.json`, test de contrat de la cellule,
  `scripts/run_hypervisor_integration.sh` (faux pool ou pool réel).
- `scripts/run_hypervisor_integration.ps1` et `GANDAL_IT_SSD_GB` pour les tests
  d'intégration sous Windows / modèle à grand disque.
- Validation sur le pool XCP-ng réel (2026-11-02) : 7 tests d'intégration verts.

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

[0.5.0]: https://github.com/Zenbx/GANDAL-SDK/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/Zenbx/GANDAL-SDK/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/Zenbx/GANDAL-SDK/compare/e4d93b9...v0.3.0
[0.2.0]: https://github.com/Zenbx/GANDAL-SDK/commit/e4d93b9
[0.1.0]: https://github.com/Zenbx/GANDAL-SDK/commit/059e98a
