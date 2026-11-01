"""Recupere le document OpenAPI d'iaas-api et l'enregistre dans openapi/.

Deux sources possibles :

    # API deja demarree
    python scripts/sync_openapi.py --url http://localhost:8000

    # depot iaas-api local, sans demarrer le serveur
    python scripts/sync_openapi.py --app-dir ../iaas-api --python ../iaas-api/.venv/bin/python

L'instantane est ecrit avec des cles triees pour que les diffs restent lisibles.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT = ROOT / "openapi" / "iaas-api.json"

# Execute dans le depot iaas-api : app.openapi() ne demarre ni base ni lifespan.
_DUMP_SNIPPET = "import json, sys; from app.main import app; json.dump(app.openapi(), sys.stdout)"

# Valeurs factices : l'import d'app.main lit la configuration sans s'en servir.
_DUMP_ENV = {"IAM_JWT_SECRET": "openapi-dump", "DATABASE_URL": "sqlite:///:memory:"}


def fetch_from_url(base_url: str) -> dict:
    """Telecharge /openapi.json depuis une instance en cours d'execution."""
    response = httpx.get(f"{base_url.rstrip('/')}/openapi.json", timeout=10.0)
    response.raise_for_status()
    return response.json()


def dump_from_app(app_dir: Path, python: str) -> dict:
    """Importe l'application FastAPI du depot iaas-api et lit son schema."""
    result = subprocess.run(
        [python, "-c", _DUMP_SNIPPET],
        cwd=app_dir,
        env={**os.environ, **_DUMP_ENV},
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise SystemExit(f"Echec de l'import d'iaas-api :\n{result.stderr}")
    return json.loads(result.stdout)


def main() -> None:
    """Point d'entree en ligne de commande."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--url", help="URL de base d'une API demarree")
    source.add_argument("--app-dir", type=Path, help="chemin du depot iaas-api")
    parser.add_argument(
        "--python",
        default=sys.executable,
        help="interpreteur ayant les dependances d'iaas-api (avec --app-dir)",
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    spec = fetch_from_url(args.url) if args.url else dump_from_app(args.app_dir, args.python)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(spec, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
    print(f"{len(spec.get('paths', {}))} routes ecrites dans {args.output}")


if __name__ == "__main__":
    main()
