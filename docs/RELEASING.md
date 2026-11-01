# Publier une version du SDK

## Numérotation

[SemVer](https://semver.org/lang/fr/). Tant que la version est en `0.x`, une
version **mineure** peut contenir des changements incompatibles ; ils sont
alors obligatoirement listés dans la section « Changements incompatibles » des
notes, avec la migration.

## Règles de commit

- Un commit par tâche minimale : une fonctionnalité, une correction, un test,
  une documentation. Une erreur découverte en cours de route a son propre
  commit de correction, avec le symptôme et la cause dans le message.
- Messages en français, à l'infinitif (« Ajouter… », « Corriger… »).
- Aucune mention d'outil de génération dans les commits, les tags ni les notes.

## Procédure

1. **Vérifier**, depuis un dépôt propre à jour de `main` :

   ```bash
   ruff check src tests scripts
   pytest
   scripts/run_integration.sh ../iaas-api ../iaas-api/.venv/bin/python
   python scripts/sync_openapi.py --app-dir ../iaas-api && git diff --exit-code openapi/
   ```

   Puis construire le paquet et le tester une fois installé :

   ```bash
   python -m build
   python -m venv /tmp/wheelenv
   /tmp/wheelenv/bin/pip install dist/*.whl pytest pytest-asyncio respx
   /tmp/wheelenv/bin/python -m pytest -q -p no:cacheprovider -o pythonpath=
   ```

2. **Changer la version** dans `pyproject.toml` et `src/gandal_sdk/__init__.py`
   (`tests/test_version.py` vérifie qu'elles concordent).

3. **Documenter** :
   - ajouter l'entrée de la version dans `CHANGELOG.md` ;
   - copier `.github/RELEASE_TEMPLATE.md` vers `docs/releases/vX.Y.Z.md` et
     remplir **toutes** les sections.

4. **Étiqueter et pousser** :

   ```bash
   git tag -a vX.Y.Z -m "GANDAL SDK vX.Y.Z"
   git push origin main vX.Y.Z
   ```

5. **Publier la release GitHub**, avec les notes et les paquets construits :

   ```bash
   gh release create vX.Y.Z dist/* \
     --title "GANDAL SDK vX.Y.Z" \
     --notes-file docs/releases/vX.Y.Z.md
   ```

6. **Contrôler** : la CI du tag est verte, et le paquet s'installe depuis le tag :

   ```bash
   pip install "git+https://github.com/Zenbx/GANDAL-SDK.git@vX.Y.Z"
   ```
