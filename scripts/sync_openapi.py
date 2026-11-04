"""Recupere le document OpenAPI d'un service GANDAL et l'enregistre dans openapi/.

Services : iaas-api (defaut), gandal-hypervisor et gandal-iam. Sources :

    # service deja demarre
    python scripts/sync_openapi.py --url http://localhost:8000

    # depot local, sans demarrer le serveur
    python scripts/sync_openapi.py --app-dir ../iaas-api --python ../iaas-api/.venv/bin/python
    python scripts/sync_openapi.py --service gandal-hypervisor --app-dir ../gandal-hypervisor \
        --python ../gandal-hypervisor/.venv/bin/python

    # IAM : contrat YAML du depot iam
    python scripts/sync_openapi.py --service gandal-iam --yaml ../iam/iam/contracts/openapi-iam.yaml

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

# Pour chaque service : code execute dans son depot, et variables d'environnement.
_SERVICES = {
    # app.openapi() ne demarre ni base ni lifespan ; la configuration lue est factice.
    "iaas-api": (
        "import json, sys; from app.main import app; json.dump(app.openapi(), sys.stdout)",
        {"IAM_JWT_SECRET": "openapi-dump", "DATABASE_URL": "sqlite:///:memory:"},
    ),
    # Le schema de la cellule se produit sans pool ni secret.
    "gandal-hypervisor": (
        "import json, sys; from gandal_hypervisor.api.schema import openapi; "
        "json.dump(openapi(), sys.stdout)",
        {"PYTHONPATH": "src"},
    ),
}

# Services dont le contrat est un fichier OpenAPI (YAML ou JSON), pas un dump d'app.
_FILE_SERVICES = frozenset({"gandal-iam"})
_ALL_SERVICES = sorted(set(_SERVICES) | _FILE_SERVICES)


def fetch_from_url(base_url: str) -> dict:
    """Telecharge /openapi.json depuis une instance en cours d'execution."""
    response = httpx.get(f"{base_url.rstrip('/')}/openapi.json", timeout=10.0)
    response.raise_for_status()
    return response.json()


def dump_from_app(app_dir: Path, python: str, service: str = "iaas-api") -> dict:
    """Importe l'application FastAPI du depot du service et lit son schema."""
    snippet, extra_env = _SERVICES[service]
    result = subprocess.run(
        [python, "-c", snippet],
        cwd=app_dir,
        env={**os.environ, **extra_env},
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise SystemExit(f"Echec de l'import de {service} :\n{result.stderr}")
    return json.loads(result.stdout)


def load_from_file(path: Path) -> dict:
    """Charge un contrat OpenAPI YAML ou JSON."""
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".yaml", ".yml"}:
        try:
            import yaml
        except ImportError as exc:  # pragma: no cover
            raise SystemExit(
                "PyYAML requis pour --yaml : pip install pyyaml"
            ) from exc
        return yaml.safe_load(text)
    return json.loads(text)


def main() -> None:
    """Point d'entree en ligne de commande."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--url", help="URL de base d'une API demarree")
    source.add_argument("--app-dir", type=Path, help="chemin du depot du service")
    source.add_argument("--yaml", type=Path, help="fichier OpenAPI YAML/JSON (gandal-iam)")
    parser.add_argument("--service", choices=_ALL_SERVICES, default="iaas-api")
    parser.add_argument(
        "--python",
        default=sys.executable,
        help="interpreteur ayant les dependances du service (avec --app-dir)",
    )
    parser.add_argument("--output", type=Path, help="defaut : openapi/<service>.json")
    args = parser.parse_args()
    output = args.output or ROOT / "openapi" / f"{args.service}.json"

    if args.url:
        spec = fetch_from_url(args.url)
    elif args.yaml:
        if args.service not in _FILE_SERVICES and args.service != "gandal-iam":
            # Autorise tout service avec --yaml, utile pour rejouer un contrat.
            pass
        spec = load_from_file(args.yaml)
    else:
        if args.service in _FILE_SERVICES:
            raise SystemExit(
                f"{args.service} s'importe avec --yaml <contrat.openap.yaml>, pas --app-dir."
            )
        spec = dump_from_app(args.app_dir, args.python, args.service)

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(spec, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
    print(f"{len(spec.get('paths', {}))} routes ecrites dans {output}")


if __name__ == "__main__":
    main()
