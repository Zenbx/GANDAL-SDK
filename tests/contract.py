"""Verification d'un client du SDK contre l'instantane OpenAPI d'un service.

Utilise par test_contract_openapi.py (iaas-api) et test_contract_hypervisor.py.
"""

from __future__ import annotations

import dataclasses
import enum
import json
import re
import types
import typing
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel

ROOT = Path(__file__).resolve().parent.parent
SDK_SOURCES = ROOT / "src" / "gandal_sdk"

_JSON_TO_PY: dict[str, tuple[type, ...]] = {
    "string": (str, datetime),
    "integer": (int,),
    "number": (float, int),
    "boolean": (bool,),
    "array": (list,),
    "object": (dict, BaseModel),
}
_CALL = re.compile(r'request\(\s*"(GET|POST|PUT|PATCH|DELETE)",\s*f?"([^"]+)"')
_PLACEHOLDER = re.compile(r"\{[^}]*\}")


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
    if typing.Any in python_types:
        return True
    if json_type == "null":
        return type(None) in python_types
    expected = _JSON_TO_PY[json_type]
    return any(isinstance(t, type) and issubclass(t, expected) for t in python_types)


def _fields(model: type) -> dict[str, tuple[object, bool]]:
    """Champs d'un modele pydantic ou d'une dataclass : nom -> (annotation, requis)."""
    if dataclasses.is_dataclass(model):
        hints = typing.get_type_hints(model)
        return {
            f.name: (
                hints[f.name],
                f.default is dataclasses.MISSING and f.default_factory is dataclasses.MISSING,
            )
            for f in dataclasses.fields(model)
        }
    return {name: (f.annotation, f.is_required()) for name, f in model.model_fields.items()}


class OpenApiContract:
    """Instantane OpenAPI d'un service, et les controles de compatibilite du SDK."""

    def __init__(self, snapshot: str) -> None:
        self.spec = json.loads((ROOT / "openapi" / snapshot).read_text())
        self.schemas = self.spec["components"]["schemas"]

    def _resolve(self, prop: dict) -> dict:
        ref = prop.get("$ref")
        return self.schemas[ref.rsplit("/", 1)[-1]] if ref else prop

    def _json_types(self, prop: dict) -> set[str]:
        """Types JSON admis par une propriete (anyOf aplati, null compris)."""
        if "anyOf" in prop:
            return set().union(*(self._json_types(option) for option in prop["anyOf"]))
        prop = self._resolve(prop)
        if "type" in prop:
            return {prop["type"]}
        if "enum" in prop:
            return {"string"}
        return {"object"}

    def model_problems(self, sdk_model: type, schema_name: str, direction: str) -> list[str]:
        """Ecarts entre un modele du SDK et un schema ; "out" = le SDK lit, "in" = il envoie."""
        schema = self.schemas[schema_name]
        properties: dict = schema.get("properties", {})
        required = set(schema.get("required", []))
        fields = _fields(sdk_model)
        problems: list[str] = []

        for name, (annotation, field_required) in fields.items():
            if name not in properties:
                # Champ lu mais jamais envoye, ou champ envoye que l'API ignore.
                if direction == "in" or field_required:
                    problems.append(f"{name}: absent du schema")
                continue
            if direction == "out" and field_required and name not in required:
                problems.append(f"{name}: requis par le SDK, facultatif dans l'API")
            python_types = _python_types(annotation)
            for json_type in self._json_types(properties[name]):
                # En sortie, le SDK doit lire tout ce que l'API peut renvoyer.
                if direction == "out" and not _accepts(python_types, json_type):
                    problems.append(
                        f"{name}: l'API renvoie {json_type}, le SDK attend {python_types}"
                    )
            if direction == "in" and not any(
                _accepts(python_types, t) for t in self._json_types(properties[name])
            ):
                problems.append(f"{name}: le SDK envoie {python_types}, refuse par l'API")

        if direction == "in":
            for name in required - set(fields):
                problems.append(f"{name}: requis par l'API, absent du SDK")
        return problems

    def missing_routes(self, sources: list[Path] | None = None) -> list[str]:
        """Routes publiees sans helper dans les sources du SDK indiquees (toutes par defaut)."""
        published = {
            (method.upper(), _PLACEHOLDER.sub("{}", path))
            for path, operations in self.spec["paths"].items()
            for method in operations
        }
        called: set[tuple[str, str]] = set()
        for source in sources or list(SDK_SOURCES.rglob("*.py")):
            for method, path in _CALL.findall(source.read_text()):
                called.add((method, _PLACEHOLDER.sub("{}", path)))
        return [f"{m} {p}" for m, p in sorted(published - called)]
