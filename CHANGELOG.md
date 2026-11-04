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

### À trancher — divergences mesurées contre le backend qui tourne

Relevées en faisant parler le vrai SDK au vrai backend
(`GANDAL-BACKEND-IaaS/iaas-api`, `f9aff99`). Elles demandent une décision à deux,
pas un choix unilatéral :

1. **`ProfileOut.id`** : le backend rend une chaîne (`String(36)`), l'instantané
   publié dit `integer`. Laissé en `int` ici, avec une note dans le modèle.
2. **L'instantané `openapi/iaas-api.json` est périmé** : 6 routes contre **46**
   servies. À resynchroniser, et cela révèle les points 3 et 4 :
   ```bash
   python scripts/sync_openapi.py --service iaas-api --app-dir <iaas-api> \
       --python <son venv>
   ```
3. **Trois modèles renommés côté backend** : `ProfileCreate`, `ProfileUpdate` et
   `PaginatedProfilesOut` ont disparu de son OpenAPI. Le test de contrat les
   cherche par nom.
4. **Six routes publiées sans helper SDK** : `GET /ready`,
   `POST /api/v1/admin/admins`, `POST /api/v1/auth/register`, et les trois
   `POST .../deletion` (projets, VM, réseaux — que le SDK appelle pourtant, mais
   que le vérificateur de couverture ne reconnaît pas).

### Ajouté

- `GardeIam` (`gandal_sdk.garde`) : la séquence du contrat IAM en un
  gestionnaire de contexte — décider → réserver → créer → confirmer, et
  **libérer** si le corps lève. La cellule `iam` savait poser la question depuis
  0.5.0 ; personne ne la posait. `orchestration/vms.py` créait, modifiait,
  allumait et détruisait des VM sans jamais demander de décision ni retenir de
  quota.
- `DecisionRefusee`, qui conserve le **motif** d'IAM et sa phrase lisible
  (« il vous reste 0 vCPU sur 4 ») au lieu d'une erreur générique.
- Stockage objet (Drive, S3, Supabase) : `autoriser_creation_seau`,
  `autoriser_suppression_seau`, `autoriser_ecriture`, `autoriser_lecture`.
  **Un projet sans quota de stockage est refusé** — c'est le défaut côté IAM, et
  il n'y a pas d'interrupteur séparé : la porte est le quota. Quel fournisseur
  (`drive`|`s3`|`supabase`) est un **attribut** du projet, pas un quota.
- 15 tests, dont les deux fautes qui ne se voient pas : créer sans confirmer, et
  échouer sans libérer.
- Instantané `openapi/gandal-iam.json` resynchronisé : `vm:update` et les six
  actions `storage:*`, plus les quatre ressources de quota du stockage.

### À savoir

- **Cette garde n'est pas le contrôle d'accès.** Un garde-fou dans un client est
  contournable : il suffit d'appeler le backend directement. Ce qu'elle apporte
  est réel — la **comptabilité** des quotas devient vraie, puisque réservation et
  confirmation se font dans IAM côté serveur — mais la *décision* reste
  consultative tant que le backend ne la demande pas lui aussi. Le contrôle qui
  fait autorité est `gandal_garde`, dans le dépôt GANDAL (`iam/garde-serveur/`).
- `autoriser_modification` **décide puis compte** : `resize_resource`
  (`POST /resources/{id}/resize`, nouveau au contrat) redimensionne la ressource
  après la décision. Elle ne comptait pas, parce que le coût du catalogue IAM
  *ajoute* et ne retranche pas — compter un redimensionnement par le chemin des
  réservations aurait compté la taille **entière** au lieu de l'écart. Les
  quantités sont **absolues** et c'est IAM qui soustrait ; les clés absentes
  restent inchangées ; seul le `stock` se redimensionne.

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
