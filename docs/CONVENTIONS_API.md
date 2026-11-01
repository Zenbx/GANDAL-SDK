# Conventions d'API GANDAL

Ce document fixe les règles que toute API consommée par le SDK doit respecter.
Elles sont communes à tous les services (orchestration, puis cellules), pour
qu'un seul SDK, un seul CLI et un seul provider d'infrastructure-as-code
puissent être construits au-dessus.

Chaque règle porte un statut :

- **en vigueur** : déjà définie dans `API_ENDPOINTS.md` d'`iaas-api` ;
- **proposée** : à valider avec l'équipe backend avant implémentation.

---

## 1. Le contrat est l'OpenAPI

**Statut : proposée.**

- La source de vérité d'un service est son document OpenAPI, produit par le
  service lui-même (FastAPI le génère sur `/openapi.json`).
- Le SDK en conserve un instantané versionné dans `openapi/`, mis à jour par
  `scripts/sync_openapi.py`.
- Un test de contrat vérifie que les modèles du SDK restent compatibles avec
  l'instantané. Une divergence casse la CI du SDK, pas la production.
- Quand l'API couvrira toute la surface de `API_ENDPOINTS.md`, les modèles du
  SDK seront générés depuis l'OpenAPI ; seule la couche de confort (paginateurs,
  attentes, identifiants) restera écrite à la main.

## 2. Versionnement

**Statut : en vigueur** pour le préfixe, **proposée** pour le reste.

- Préfixe `/api/v1`.
- À l'intérieur d'une version, seuls les changements **additifs** sont permis :
  nouvelle route, nouveau champ de réponse, nouveau champ de requête optionnel.
- Supprimer ou renommer un champ, rendre un champ obligatoire, changer un type
  ou un code d'erreur exige `/api/v2`.
- Le SDK ignore les champs de réponse inconnus : un ajout côté API ne doit
  jamais casser un client existant.

## 3. Identifiants de ressources

**Statut : proposée.**

Chaque ressource garde son identifiant court (`vm-…`, `prj-…`), et expose en
plus un nom global, sur le modèle des ARN d'AWS :

```
grn:gandal:<service>:<projet>:<type>/<id>

grn:gandal:compute:prj-42:vm/vm-7f3a
grn:gandal:storage:prj-42:volume/vol-19c2
grn:gandal:network:prj-42:network/net-03
```

Le GRN sert dans les politiques d'autorisation, les journaux d'audit et les
références entre services. Il est renvoyé dans le champ `grn` de chaque
ressource, en lecture seule.

## 4. Erreurs

**Statut : en vigueur** pour le format, **proposée** pour les en-têtes.

Format unique :

```json
{ "error": { "code": "forbidden", "message": "…", "details": null } }
```

Le SDK lève `GandalApiError` avec `code`, `message`, `details` et `status`.
Les codes sont ceux de `API_ENDPOINTS.md` §1.4 ; le SDK s'appuie sur `code`,
jamais sur le texte de `message`.

Ajouts proposés :

| En-tête | Sens |
|---|---|
| `X-Request-Id` | identifiant unique de la requête, renvoyé sur toute réponse, cité dans les journaux du serveur |
| `Retry-After` | sur `429` et `503`, délai en secondes avant de réessayer |

## 5. Relances

**Statut : proposée.**

Le SDK réessaie automatiquement, avec attente exponentielle et gigue
(3 tentatives par défaut) :

| Réponse | `GET`, `PUT`, `DELETE` | `POST`, `PATCH` |
|---|---|---|
| `429 throttled` (nouveau code, à ajouter au catalogue) | oui | oui : la requête a été refusée avant traitement |
| `503 upstream_unavailable` | oui | **seulement** avec une clé d'idempotence (§6) |
| erreur réseau ou délai dépassé | oui | **seulement** avec une clé d'idempotence (§6) |
| tout autre `4xx` | jamais | jamais |

`Retry-After` est respecté quand il est présent.

Pourquoi cette prudence sur `503` : `API_ENDPOINTS.md` garantit qu'un `503`
n'annonce aucun succès, mais pas qu'aucun effet externe n'a eu lieu. Rejouer
un `POST` sans clé d'idempotence pourrait créer un doublon.

## 6. Idempotence

**Statut : proposée.**

Toute création (`POST`) accepte l'en-tête `Idempotency-Key` (UUID fourni par le
client). Le serveur mémorise la réponse pendant 24 h : une requête rejouée avec
la même clé et le même corps renvoie la même réponse sans recréer la ressource.
Même clé avec un corps différent : `409 conflict`.

Quand le serveur la prendra en charge, le SDK générera cette clé lui-même, ce
qui rendra sûres les relances de `POST`. C'est l'équivalent du `ClientToken`
d'EC2. D'ici là, le SDK n'en envoie pas : un serveur qui ignore la clé
transformerait chaque relance en doublon.

## 7. Opérations longues

**Statut : proposée.**

Créer, redimensionner, migrer ou supprimer une VM ou un volume prend du temps et
peut échouer à mi-parcours. Ces actions ne bloquent pas la requête HTTP :

1. le serveur répond `202 Accepted` avec la ressource dans un état transitoire
   (`creating`, `stopping`…) et un objet `operation` ;
2. l'opération est consultable sur `GET /api/v1/operations/{operation_id}` :

```json
{
  "id": "op-5b1e",
  "status": "running",
  "resource_grn": "grn:gandal:compute:prj-42:vm/vm-7f3a",
  "action": "vm.create",
  "created_at": "2026-11-01T10:00:00Z",
  "updated_at": "2026-11-01T10:00:04Z",
  "error": null
}
```

`status` vaut `pending`, `running`, `succeeded` ou `failed`.

À ne pas confondre avec les **demandes** (`RequestOut`, déjà en vigueur), qui
renvoient aussi `202` : une demande attend une **décision humaine** d'un
administrateur ; une opération suit l'**exécution technique** sur le pool. Une
demande approuvée déclenche une opération. En cas d'échec,
`error` suit le format du §4.

Côté SDK, des fonctions d'attente masquent l'interrogation :
`client.orchestration.vms.wait_until_running(project_id, vm_id)`, qui lève une
erreur explicite sur `failed` ou à l'expiration du délai.

## 8. Pagination

**Statut : en vigueur.**

Pagination par numéro de page (`page`, `page_size` ≤ 100), enveloppe
`items / page / page_size / total_items / total_pages`.

Le SDK fournit `paginate`, qui parcourt toutes les pages de n'importe quelle
méthode de liste, pour que l'appelant n'ait pas à gérer les numéros :

```python
from gandal_sdk import paginate

for vm in paginate(client.orchestration.vms.list, project_id, state="running"):
    ...
```

Un curseur opaque (`next_token`) sera plus robuste quand les listes changeront
pendant le parcours. Il pourra être ajouté en v1 sans rupture, comme champ
supplémentaire.

## 9. Authentification et identifiants

**Statut : en vigueur** pour le jeton Bearer, **proposée** pour le reste.

Aujourd'hui : `Authorization: Bearer <jeton>` obtenu par `/auth/login`.

Pour les applications et les scripts, un mot de passe n'est pas le bon outil.
Il est proposé d'ajouter :

- des **clés d'accès** par utilisateur ou compte de service (identifiant public
  + secret, révocables, avec date d'expiration), échangées contre un jeton
  court ;
- une **chaîne de résolution** dans le SDK, comme chez AWS, dans cet ordre :
  1. paramètres passés explicitement au client ;
  2. variables d'environnement `GANDAL_ENDPOINT`, `GANDAL_TOKEN`,
     `GANDAL_ACCESS_KEY_ID`, `GANDAL_SECRET_ACCESS_KEY` ;
  3. profil de `~/.gandal/credentials` (choisi par `GANDAL_PROFILE`,
     `default` sinon).

Le secret n'est jamais écrit dans les journaux ni dans les messages d'erreur du
SDK.

## 10. Dates, noms et formats

**Statut : en vigueur.**

- Dates en ISO 8601, UTC, avec suffixe `Z`.
- Champs en `snake_case`, valeurs d'énumération en minuscules.
- Corps JSON ; `204` sans corps pour les suppressions sans réponse.
