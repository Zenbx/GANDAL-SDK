# Instructions de reprise — SDK GANDAL et cellule hyperviseur

Document de passation, à jour au 2026-11-01. Il décrit où en est le projet, comment
travailler dessus, et quoi faire ensuite. Lire en entier avant de commencer.

> **Avant toute chose**
> 1. Le dépôt `gandal-hypervisor` est **privé** : demander à Bala une invitation
>    (GitHub → Settings → Collaborators) avant de pouvoir le cloner.
> 2. Le mot de passe root XAPI du pool n'est écrit **nulle part** dans les dépôts.
>    Il se transmet de vive voix ou par un canal chiffré, jamais par Git ni chat.
> 3. Ne jamais lancer de test sur le pool sans être passé par le contrôle préalable
>    (§5, étape 3).

---

## 1. Objectif

Construire un SDK « à la AWS » pour la plateforme GANDAL, qui pilote réellement le
pool XCP-ng **rem / jade / emilia** (stockage XOSTOR/LINSTOR). Un client écrit :

```python
created = client.hypervisor.create_vm(VmSpec(name="sdk-it-web", ram_gb=1, vcpu=1, vram_gb=0, ssd_gb=10))
vm = client.hypervisor.wait_until_running(created.vm)
```

et une VM est clonée, configurée et démarrée sur le pool.

## 2. Où en est-on

| Maillon | État |
| --- | --- |
| SDK Python (GANDAL-SDK) | v0.4.0 : hyperviseur publié ; validé faux pool + pool réel (2026-11-02) |
| Cellule hyperviseur (gandal-hypervisor) | complète ; testée faux pool **et** pool réel (bac à sable) |
| Pool XCP-ng réel | premier passage SDK réussi ; snapshot homonyme renommé `gandal-reference-snap` |
| iaas-api (équipe backend) | publie seulement l'authentification et les profils ; pas encore branché à la cellule |

**Prochaine priorité :** publier / consolider (§6), puis R1, ops persistantes, CI cellule.

## 3. Les dépôts

| Dépôt | Rôle | Propriétaire | Ce qu'on peut y faire |
| --- | --- | --- | --- |
| [Zenbx/GANDAL-SDK](https://github.com/Zenbx/GANDAL-SDK) (public) | SDK Python, ce fichier | Zenbx | travailler librement |
| [BalaAndegue/gandal-hypervisor](https://github.com/BalaAndegue/gandal-hypervisor) (privé) | service HTTP qui pilote les VM via XAPI | Bala | travailler librement |
| [GANDAL-BACKEND-IaaS/iaas-api](https://github.com/GANDAL-BACKEND-IaaS/iaas-api) | API métier (projets, demandes, IAM) | équipe backend | **ne pas modifier** ; leur remonter les écarts (§8) |
| Zenbx/gandal-cli (Go) | CLI d'administration XenAPI | Zenbx | outil d'exploitation, hors chemin du SDK |
| gandal-ctl (Python, sur la machine de Bala, dans aucun dépôt Git) | surveillance, invariants, évacuation d'hôte | Bala | référence pour les règles du pool (R1–R4) ; demander une copie |

Architecture :

```
SDK (client.hypervisor) ──HTTP + jeton──► gandal-hypervisor ──XAPI/TLS──► maître du pool ──► rem / jade / emilia
SDK (client.orchestration) ──HTTP + JWT──► iaas-api            (plus tard : iaas-api ──► gandal-hypervisor)
```

Les dépôts doivent être clonés **côte à côte** : les scripts les trouvent par `../`.

```bash
mkdir ~/gandal && cd ~/gandal
git clone https://github.com/Zenbx/GANDAL-SDK.git
git clone https://github.com/BalaAndegue/gandal-hypervisor.git
git clone https://github.com/GANDAL-BACKEND-IaaS/iaas-api.git
```

## 4. Mise en route et vérification

Python 3.11 minimum.

```bash
# Cellule
cd ~/gandal/gandal-hypervisor
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
.venv/bin/ruff check src tests && .venv/bin/pytest -q        # 79 tests attendus

# SDK
cd ~/gandal/GANDAL-SDK
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
.venv/bin/ruff check src tests scripts && .venv/bin/pytest -q # 104 réussis, 19 ignorés

# iaas-api (pour les tests d'intégration de l'orchestration)
cd ~/gandal/iaas-api
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt

# Intégrations, depuis GANDAL-SDK (ajouter .venv/bin au PATH)
export PATH=$PWD/.venv/bin:$PATH
scripts/run_integration.sh ../iaas-api ../iaas-api/.venv/bin/python   # 12 tests, vraie iaas-api
scripts/run_hypervisor_integration.sh ../gandal-hypervisor            # 7 tests, vraie cellule, faux pool
```

Si l'un de ces résultats diffère, s'arrêter et comprendre pourquoi avant de
continuer.

Lancer la cellule à la main sur le faux pool (pour essayer le SDK) :

```bash
mkdir -p ~/.gandal && (umask 077 && head -c 32 /dev/urandom | base64 > ~/.gandal/hv-token)
cd ~/gandal/gandal-hypervisor
GANDAL_HV_FAKE=1 GANDAL_HV_TOKEN_FILE=~/.gandal/hv-token .venv/bin/python -m gandal_hypervisor
# puis : GANDAL_HYPERVISOR_ENDPOINT=http://127.0.0.1:8770 GANDAL_HYPERVISOR_TOKEN=$(cat ~/.gandal/hv-token)
```

## 5. Tâche prioritaire : premier passage sur le pool réel

Objectif : faire passer les **mêmes** tests d'intégration contre le vrai pool. La
procédure détaillée est dans le README de gandal-hypervisor, section « Premier
passage sur le pool réel ». En résumé :

1. **Être sur le réseau du pool** (`192.168.123.x`). Hôtes : emilia `.100`,
   jade `.101`, rem `.102`. Vérifier : `timeout 3 bash -c '</dev/tcp/192.168.123.100/443' && echo joignable`.
2. **Préparer les secrets** dans `~/.gandal/`, en `chmod 600` :
   - `pool-ca.pem` : les certificats des **trois** hôtes concaténés, empreintes
     comparées à celles lues sur chaque hôte ;
   - `xapi-password` : le mot de passe root XAPI.
3. **Contrôle préalable, lecture seule** — aucune VM n'est créée :

   ```bash
   cd ~/gandal/gandal-hypervisor
   export GANDAL_HV_PASSWORD_FILE=~/.gandal/xapi-password GANDAL_HV_CA_FILE=~/.gandal/pool-ca.pem
   .venv/bin/python -m gandal_hypervisor.preflight
   ```

   Tout doit être `[OK]`. Sinon, voir le tableau ci-dessous et **ne pas aller plus loin**.
4. **Bout en bout**, en bac à sable (VM `sdk-it-*`, 1 vCPU, 1 Go, 2 au plus,
   supprimées à la fin) :

   ```bash
   cd ~/gandal/GANDAL-SDK
   GANDAL_HV_FAKE=0 GANDAL_IT_DELAY=5 scripts/run_hypervisor_integration.sh ../gandal-hypervisor
   ```

   La première ligne affichée doit indiquer `pool 192.168.123.100, ...` et non
   `FAUX POOL`.
5. **Vérifier qu'il ne reste rien** et que les invariants tiennent :

   ```bash
   ssh root@<maitre> "xe vm-list params=name-label --minimal | tr , '\\n' | grep '^sdk-it-'"   # aucune ligne
   ./gandal-ctl check
   ```

| Symptôme | Cause probable | Action |
| --- | --- | --- |
| `CERTIFICATE_VERIFY_FAILED` sur un hôte | son certificat manque dans `pool-ca.pem` | ajouter le certificat de cet hôte, vérifier son empreinte |
| `identifiants refuses` | mot de passe erroné | corriger `xapi-password` ; ne pas réessayer en boucle |
| modèle : `0 VM portent ce nom` ou `2 VM` | `gandal-reference` absent ou en double | demander à Bala ; régler `GANDAL_HV_TEMPLATE` si un autre modèle est prévu |
| modèle : `doit etre arrete` | `gandal-reference` tourne | l'arrêter (c'est une VM de référence, pas un service) |
| `VM deja gerees` KO | VM `sdk-it-*` restées d'un essai précédent | les supprimer via la cellule ou `xe`, puis relancer |
| création : `validation_error` sur `ssd_gb` | le disque du modèle dépasse 10 Go | le message donne le minimum ; ajuster `ssd_gb` dans `tests/integration_hypervisor` |
| délai dépassé (`WaiterTimeout`) | clonage XOSTOR plus lent que prévu | augmenter `GANDAL_IT_DELAY` / `GANDAL_IT_MAX_ATTEMPTS` |
| code XAPI inattendu | comportement réel différent du faux pool | voir ci-dessous |

**Le faux pool doit suivre le vrai.** Les codes d'erreur marqués « à confirmer »
dans `gandal-hypervisor/src/gandal_hypervisor/xapi/fake.py` n'ont jamais été
observés en réel. Toute différence constatée sur le pool se corrige **d'abord dans
le faux** (avec un test), **ensuite** dans l'adaptateur : sinon les tests continuent
de valider un comportement qui n'existe pas.

Points à observer pendant ce premier passage et à noter dans le compte rendu :
durée d'un clonage sur XOSTOR, hôte choisi par XAPI au démarrage, présence d'une
IP (agent invité dans le modèle), comportement de `clean_shutdown`.

## 6. Ensuite, par ordre de priorité

1. **Publier le SDK 0.4.0** une fois le passage réel réussi (procédure :
   `docs/RELEASING.md`, canevas : `.github/RELEASE_TEMPLATE.md`, entrées déjà
   prêtes dans la section « Non publié » de `CHANGELOG.md`). Y consigner les
   résultats du pool réel.
2. **Règle R1 à la création** : démarrer la VM sur l'hôte qui porte son disque
   système (`VM.start_on`). Aujourd'hui XAPI choisit seul ; gandal-ctl signale
   l'écart a posteriori. Voir `gandal-ctl/invariants.py`.
3. **Historique des opérations persistant** (SQLite) : un redémarrage de la
   cellule perd aujourd'hui les opérations en cours et les créations échouées.
4. **CI du SDK contre la cellule** : impossible tant que gandal-hypervisor est
   privé. Soit le rendre public, soit ajouter un jeton GitHub en lecture seule
   (limité à ce dépôt) dans les secrets de Zenbx/GANDAL-SDK, puis un job qui lance
   `scripts/run_hypervisor_integration.sh`.
5. **Console** : nécessite un relais authentifié ; l'URL de console XAPI embarque
   une session root et ne doit **jamais** être renvoyée au client.
6. **Brancher iaas-api sur la cellule** : à proposer à l'équipe backend (leur port
   hyperviseur appellerait `gandal-hypervisor`). Le contrat est
   `openapi/gandal-hypervisor.json`.
7. Plus tard : PyPI pour le SDK Python ; SDK TypeScript (npm) généré depuis
   l'OpenAPI ; quotas et sortie du bac à sable (`GANDAL_HV_POLICY=unrestricted`).

## 7. Règles de travail

**Commits**
- Un commit par tâche minimale : une fonctionnalité, une correction, un test, une
  documentation, un reformatage. Une erreur découverte en route a **son propre**
  commit, avec le symptôme et la cause dans le message.
- Messages en français, à l'infinitif (« Ajouter… », « Corriger… »).
- **Aucune mention d'outil de génération ou d'IA** dans les commits, tags, notes
  de release ou fichiers (pas de `Co-Authored-By` automatique).
- `git add <fichiers>` plutôt que `git add -A` : on a déjà embarqué par erreur un
  fichier non testé dans un commit sans rapport.

**Tests, au plus près du réel**
- Chaque correction de bug commence par un test qui échoue.
- Préférer de vraies sockets, de vrais processus et de vrais serveurs TLS aux
  mocks quand c'est possible (exemples : `tests/test_retry_live.py`,
  `gandal-hypervisor/tests/test_tls_live.py`).
- Une course entre threads se reproduit de façon **déterministe** (voir
  `test_get_survives_creation_finishing_mid_read`), pas par un test de charge au
  hasard.
- Vérifier qu'un test de sécurité sert à quelque chose en cassant
  volontairement le code (test par mutation) : c'est ainsi qu'on a trouvé que la
  protection des ISO n'était pas couverte.

**Contrats**
- `openapi/*.json` sont des instantanés des services. Après un changement d'API :
  `python scripts/sync_openapi.py --help`, puis `pytest tests/test_contract_*.py`.
- Les erreurs suivent l'enveloppe `{error: {code, message, details}}` de
  `docs/CONVENTIONS_API.md`. La cellule la respecte ; iaas-api pas encore (le SDK
  s'adapte en déduisant le code du statut HTTP).

**Sécurité**
- Secrets uniquement dans des fichiers `chmod 600`, hors des dépôts ; la cellule
  refuse de démarrer sinon.
- TLS toujours vérifié ; ne jamais ajouter d'option pour le désactiver.
- La cellule ne doit jamais voir ni toucher une VM sans le marqueur
  `other_config:gandal_managed=true`. Tout changement dans `xapi/compute.py` doit
  garder les tests `test_unmanaged_vms_are_invisible`,
  `test_failed_creation_leaves_nothing_behind` et
  `test_iso_used_only_by_deleted_vm_survives` au vert.

## 8. Décisions déjà prises (ne pas rouvrir sans raison nouvelle)

| Décision | Pourquoi |
| --- | --- |
| Cellule hyperviseur séparée, à nous, plutôt qu'une PR dans iaas-api | avancer sans dépendre du backend ; iaas-api s'y branchera par son port |
| Le SDK ne parle jamais XAPI directement | sinon chaque client aurait le mot de passe root du pool |
| Bac à sable par défaut | premier contact avec un pool de production |
| Une session XAPI neuve par opération | le maître se déplace (bascules, maintenance de rem) |
| Mémoire `dynamic_min < dynamic_max` | règle R4 de gandal-ctl : sans ballooning, 18 VM au lieu de 90 |
| Faux pool au niveau des appels XAPI | le vrai code de l'adaptateur s'exécute dans les tests |
| `profile_id` et `request_id` entiers | c'est ce que renvoie l'API réelle (bug corrigé en 0.3.0) |
| Pas de SDK npm pour l'instant | il faut un SDK TypeScript distinct ; priorité au fonctionnement réel |

Écarts à remonter à l'équipe iaas-api (déjà listés dans `docs/releases/v0.3.0.md`) :
format d'erreur FastAPI au lieu de l'enveloppe documentée, `/api/v1/health`
absente, dépendances non épinglées, propositions de `docs/CONVENTIONS_API.md` à
valider.

## 9. Pièges connus

- `pkill -f <motif>` tue aussi le shell qui contient le motif : arrêter un serveur
  par son port (`ss -ltnp | grep :8770`).
- Les scripts d'intégration refusent un port déjà occupé, pour ne jamais tester
  contre un serveur résiduel.
- `xe vm-list name-label=X` cherche un nom **exact**.
- Une nouvelle version de FastAPI change l'OpenAPI d'iaas-api sans changement de
  code : le job `openapi-drift` peut échouer pour cette seule raison ; relancer
  `scripts/sync_openapi.py` et committer l'instantané.
- Le modèle `gandal-reference` doit rester **arrêté** : XAPI ne clone pas une VM
  en marche.

## 10. Références

- `README.md` (SDK) et `docs/CONVENTIONS_API.md` : usage et règles d'API.
- `gandal-hypervisor/README.md` : garanties, API, configuration, procédure pool.
- `docs/RELEASING.md`, `CHANGELOG.md`, `docs/releases/` : publication.
- `gandal-ctl/README.md` : invariants R1–R4, pièges LINSTOR, procédure `drain`.
