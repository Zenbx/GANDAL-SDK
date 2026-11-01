"""Compatibilite du SDK avec l'instantane OpenAPI d'iaas-api (openapi/iaas-api.json).

Seules les routes deja publiees par l'API sont verifiees : le SDK couvre aussi
des routes de API_ENDPOINTS.md qui ne sont pas encore implementees.
Mettre a jour l'instantane : python scripts/sync_openapi.py --help
"""

from __future__ import annotations

import pytest
from contract import OpenApiContract
from pydantic import BaseModel

from gandal_sdk.orchestration import auth, models

CONTRACT = OpenApiContract("iaas-api.json")

# (modele du SDK, schema de l'API, sens) ; "out" = le SDK lit, "in" = le SDK envoie.
MODEL_PAIRS: list[tuple[type[BaseModel], str, str]] = [
    (auth.TokenOut, "TokenOut", "out"),
    (auth.IdentityOut, "IdentityOut", "out"),
    (auth.LoginIn, "LoginIn", "in"),
    (models.UserUpdateIn, "UserUpdateIn", "in"),
    (models.PasswordChangeIn, "PasswordChangeIn", "in"),
    (models.RightOut, "RightOut", "out"),
    (models.ProfileOut, "ProfileOut", "out"),
    (models.ProfileCreateIn, "ProfileCreate", "in"),
    (models.ProfileUpdateIn, "ProfileUpdate", "in"),
    (models.Page[models.ProfileOut], "PaginatedProfilesOut", "out"),
]


@pytest.mark.parametrize(
    ("sdk_model", "schema_name", "direction"),
    MODEL_PAIRS,
    ids=[name for _, name, _ in MODEL_PAIRS],
)
def test_model_matches_schema(sdk_model: type[BaseModel], schema_name: str, direction: str) -> None:
    """Champs et types du SDK compatibles avec le schema publie par l'API."""
    problems = CONTRACT.model_problems(sdk_model, schema_name, direction)
    assert not problems, f"{sdk_model.__name__} <> {schema_name} :\n  " + "\n  ".join(problems)


def test_every_published_route_is_covered_by_sdk() -> None:
    """Toute route publiee par l'API a un helper dans le SDK."""
    missing = CONTRACT.missing_routes()
    assert not missing, "Routes de l'API sans helper SDK :\n  " + "\n  ".join(missing)
