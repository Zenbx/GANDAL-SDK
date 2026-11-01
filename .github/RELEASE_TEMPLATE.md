# GANDAL SDK vX.Y.Z

<!--
Canevas des notes de release. Copier dans docs/releases/vX.Y.Z.md, remplir
chaque section, puis publier (voir docs/RELEASING.md).
Une section sans contenu reste presente avec « Aucun. » : son absence ne doit
jamais laisser croire qu'on a oublie de la remplir.
-->

**Date :** AAAA-MM-JJ · **Version précédente :** vX.Y.Z · **Type :** majeure | mineure | correctif

## Résumé

<!-- Deux à quatre phrases : ce que cette version apporte et à qui. -->

## ⚠️ Changements incompatibles et migration

<!--
Tout ce qui peut casser un code appelant existant : type modifié, valeur de
retour ou exception différente, comportement par défaut changé.
Pour chacun : avant, après, et le code à modifier.
-->

| Changement | Avant | Après | Action requise |
| --- | --- | --- | --- |

## Nouveautés

<!-- Une ligne par fonctionnalité, avec un exemple d'usage si elle est publique. -->

## Corrections

<!-- Le symptôme observé par l'utilisateur, la cause, le correctif. -->

## Documentation

## Qualité, tests et CI

<!-- Ce qui est vérifié, et contre quoi (mocks, vraie API, paquet installé). -->

## Compatibilité

| Élément | Version |
| --- | --- |
| Python | |
| iaas-api (commit vérifié) | |
| Instantané OpenAPI | |
| Dépendances | |

## Installation

```bash
pip install "git+https://github.com/Zenbx/GANDAL-SDK.git@vX.Y.Z"
```

## Vérifications effectuées avant publication

- [ ] `ruff check src tests scripts`
- [ ] `pytest` (tests unitaires)
- [ ] `scripts/run_integration.sh` contre iaas-api au commit indiqué
- [ ] tests sur le wheel installé dans un environnement vierge
- [ ] Python minimal supporté
- [ ] aucune dérive de l'instantané OpenAPI

## Limites connues

<!-- Ce qui ne marche pas encore, ou seulement à certaines conditions. -->

## Retours à faire aux autres équipes

<!-- Écarts constatés chez les services consommés (iaas-api, cellules). -->

## Liste des commits

<!-- git log --reverse --format='- %h %s' vPRECEDENTE..vX.Y.Z -->
