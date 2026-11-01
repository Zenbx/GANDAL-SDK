"""Compatibilite du SDK avec l'instantane OpenAPI d'iaas-api (openapi/iaas-api.json).

Seules les routes deja publiees par l'API sont verifiees : le SDK couvre aussi
des routes de API_ENDPOINTS.md qui ne sont pas encore implementees.
Mettre a jour l'instantane : python scripts/sync_openapi.py --help
"""

from __future__ import annotations

import enum
import json
import re
import types
import typing
from datetime import datetime
from pathlib import Path

import pytest
from pydantic import BaseModel

from gandal_sdk.orchestration import auth, models

ROOT = Path(__file__).resolve().parent.parent
SPEC = json.loads((ROOT / "openapi" / "iaas-api.json").read_text())
SCHEMAS = SPEC["components"]["schemas"]
SDK_SOURCES = ROOT / "src" / "gandal_sdk"

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

_JSON_TO_PY: dict[str, tuple[type, ...]] = {
    "string": (str, datetime),
    "integer": (int,),
    "number": (float, int),
    "boolean": (bool,),
    "array": (list,),
    "object": (dict, BaseModel),
}


def _resolve(prop: dict) -> dict:
    """Suit une reference $ref vers components/schemas."""
    ref = prop.get("$ref")
    return SCHEMAS[ref.rsplit("/", 1)[-1]] if ref else prop


def _json_types(prop: dict) -> set[str]:
    """Types JSON admis par une propriete (anyOf aplati, null compris)."""
    if "anyOf" in prop:
        return set().union(*(_json_types(option) for option in prop["anyOf"]))
    prop = _resolve(prop)
    if "type" in prop:
        return {prop["type"]}
    if "enum" in prop:
        return {"string"}
    return {"object"}


def _python_types(annotation: object) -> set[type]:
    """Types Python acceptes par une annotation (union, Optional, Literal aplatis)."""
    origin = typing.get_origin(annotation)
    if origin in (typing.Union, types.UnionType):
        return set().union(*(_python_types(arg) for arg in typing.get_args(annotation)))
    if origin is typing.Literal:
        return {type(value) for value in typing.get_args(annotation)}
    if origin is not None:
        return {origin}
    if annotation is None or annotation is type(None):
        return {type(None)}
    if isinstance(annotation, type) and issubclass(annotation, enum.Enum):
        return {str} if issubclass(annotation, str) else {annotation}
    return {annotation}  # type: ignore[arg-type]


def _accepts(python_types: set[type], json_type: str) -> bool:
    """Le modele du SDK sait-il lire ou ecrire ce type JSON ?"""
    if json_type == "null":
        return type(None) in python_types
    expected = _JSON_TO_PY[json_type]
    return any(isinstance(t, type) and issubclass(t, expected) for t in python_types)


@pytest.mark.parametrize(
    ("sdk_model", "schema_name", "direction"),
    MODEL_PAIRS,
    ids=[name for _, name, _ in MODEL_PAIRS],
)
def test_model_matches_schema(sdk_model: type[BaseModel], schema_name: str, direction: str) -> None:
    """Champs et types du SDK compatibles avec le schema publie par l'API."""
    schema = SCHEMAS[schema_name]
    properties: dict = schema.get("properties", {})
    required = set(schema.get("required", []))
    fields = sdk_model.model_fields
    problems: list[str] = []

    for name, field in fields.items():
        if name not in properties:
            # Champ lu mais jamais envoye, ou champ envoye que l'API ignore.
            if direction == "in" or field.is_required():
                problems.append(f"{name}: absent du schema")
            continue
        if direction == "out" and field.is_required() and name not in required:
            problems.append(f"{name}: requis par le SDK, facultatif dans l'API")
        python_types = _python_types(field.annotation)
        for json_type in _json_types(properties[name]):
            # En sortie, le SDK doit lire tout ce que l'API peut renvoyer.
            if direction == "out" and not _accepts(python_types, json_type):
                problems.append(f"{name}: l'API renvoie {json_type}, le SDK attend {python_types}")
        if direction == "in" and not any(
            _accepts(python_types, t) for t in _json_types(properties[name])
        ):
            problems.append(f"{name}: le SDK envoie {python_types}, refuse par l'API")

    if direction == "in":
        for name in required - set(fields):
            problems.append(f"{name}: requis par l'API, absent du SDK")

    assert not problems, f"{sdk_model.__name__} <> {schema_name} :\n  " + "\n  ".join(problems)


_CALL = re.compile(r'request\(\s*"(GET|POST|PUT|PATCH|DELETE)",\s*f?"([^"]+)"')
_PLACEHOLDER = re.compile(r"\{[^}]*\}")


def _sdk_operations() -> set[tuple[str, str]]:
    """Couples (methode, chemin) appeles par le SDK, parametres normalises."""
    found: set[tuple[str, str]] = set()
    for source in SDK_SOURCES.rglob("*.py"):
        for method, path in _CALL.findall(source.read_text()):
            found.add((method, _PLACEHOLDER.sub("{}", path)))
    return found


def test_every_published_route_is_covered_by_sdk() -> None:
    """Toute route publiee par l'API a un helper dans le SDK."""
    published = {
        (method.upper(), _PLACEHOLDER.sub("{}", path))
        for path, operations in SPEC["paths"].items()
        for method in operations
    }
    missing = sorted(published - _sdk_operations())
    assert not missing, "Routes de l'API sans helper SDK :\n  " + "\n  ".join(
        f"{m} {p}" for m, p in missing
    )
