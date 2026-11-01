"""Resolution de l'endpoint et du jeton (docs/CONVENTIONS_API.md §9).

Ordre de priorite, champ par champ :

1. valeurs passees explicitement ;
2. variables d'environnement GANDAL_ENDPOINT et GANDAL_TOKEN ;
3. profil du fichier ~/.gandal/credentials (GANDAL_CREDENTIALS_FILE pour un autre
   chemin), choisi par l'argument profile, sinon GANDAL_PROFILE, sinon « default ».

Exemple de fichier :

    [default]
    endpoint = https://api.gandal.example
    token = eyJhbGciOi...

    [admin]
    endpoint = https://api.gandal.example
    token = eyJhbGciOi...
"""

from __future__ import annotations

import configparser
import os
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

from gandal_sdk.errors import GandalError

DEFAULT_PROFILE = "default"


@dataclass(frozen=True)
class Credentials:
    """Endpoint de l'API et jeton Bearer eventuel."""

    endpoint: str
    token: str | None = field(default=None, repr=False)  # jamais affiche


def default_credentials_path(environ: Mapping[str, str] | None = None) -> Path:
    """Chemin du fichier d'identifiants : GANDAL_CREDENTIALS_FILE ou ~/.gandal/credentials."""
    env = os.environ if environ is None else environ
    override = env.get("GANDAL_CREDENTIALS_FILE")
    return Path(override) if override else Path.home() / ".gandal" / "credentials"


def _read_profile(path: Path, profile: str, *, required: bool) -> Mapping[str, str]:
    """Lit une section du fichier ; vide si absente et non exigee."""
    parser = configparser.ConfigParser()
    if not parser.read(path, encoding="utf-8"):
        if required:
            raise GandalError(f"Profil '{profile}' demande, mais {path} est introuvable.")
        return {}
    if not parser.has_section(profile):
        if required:
            raise GandalError(f"Profil '{profile}' absent de {path}.")
        return {}
    return parser[profile]


def resolve_credentials(
    *,
    endpoint: str | None = None,
    token: str | None = None,
    profile: str | None = None,
    path: Path | None = None,
    environ: Mapping[str, str] | None = None,
) -> Credentials:
    """Applique la chaine de resolution et renvoie l'endpoint et le jeton retenus."""
    env = os.environ if environ is None else environ
    chosen_profile = profile or env.get("GANDAL_PROFILE")
    file_values = _read_profile(
        path or default_credentials_path(env),
        chosen_profile or DEFAULT_PROFILE,
        # Un profil nomme doit exister ; « default » implicite est facultatif.
        required=chosen_profile is not None,
    )

    resolved_endpoint = endpoint or env.get("GANDAL_ENDPOINT") or file_values.get("endpoint")
    if not resolved_endpoint:
        raise GandalError(
            "Aucun endpoint GANDAL : passer endpoint=, definir GANDAL_ENDPOINT "
            "ou renseigner endpoint dans ~/.gandal/credentials."
        )
    resolved_token = token or env.get("GANDAL_TOKEN") or file_values.get("token") or None
    return Credentials(endpoint=resolved_endpoint, token=resolved_token)
