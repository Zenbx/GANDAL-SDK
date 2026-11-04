"""Compatibilite du client IAM avec l'instantane openapi/gandal-iam.json."""

from __future__ import annotations

import pytest
from contract import SDK_SOURCES, OpenApiContract

from gandal_sdk.cells import iam

CONTRACT = OpenApiContract("gandal-iam.json")

# (modele du SDK, schema de la cellule, sens) ; "out" = le SDK lit, "in" = le SDK envoie.
MODEL_PAIRS: list[tuple[type, str, str]] = [
    (iam.DemandeDecision, "DemandeDecision", "in"),
    (iam.Decision, "Decision", "out"),
    (iam.Sujet, "Sujet", "out"),
    (iam.Projet, "Projet", "out"),
    (iam.Membre, "Membre", "out"),
    (iam.DemandeAcces, "DemandeAcces", "out"),
    (iam.Quotas, "Quotas", "out"),
    (iam.Reservation, "Reservation", "out"),
    (iam.Proposition, "Proposition", "out"),
    (iam.Agregats, "Agregats", "out"),
    (iam.EvenementAudit, "EvenementAudit", "out"),
    (iam.Action, "Action", "out"),
    (iam.PolitiqueEntree, "PolitiqueEntree", "in"),
    (iam.RoleEntree, "RoleEntree", "in"),
    (iam.MachineEntree, "MachineEntree", "in"),
    (iam.CleEntree, "CleEntree", "in"),
    (iam.DemandeAssomption, "DemandeAssomption", "in"),
    (iam.DroitEntree, "DroitEntree", "in"),
    (iam.AttributsEntree, "AttributsEntree", "in"),
    (iam.MembreNouveau, "MembreNouveau", "in"),
]


@pytest.mark.parametrize(
    ("sdk_model", "schema_name", "direction"),
    MODEL_PAIRS,
    ids=[name for _, name, _ in MODEL_PAIRS],
)
def test_model_matches_schema(sdk_model: type, schema_name: str, direction: str) -> None:
    problems = CONTRACT.model_problems(sdk_model, schema_name, direction)
    assert not problems, f"{sdk_model.__name__} <> {schema_name} :\n  " + "\n  ".join(problems)


def test_enums_cover_contract() -> None:
    """Les enumerations du SDK couvrent les valeurs que IAM peut renvoyer."""
    schemas = CONTRACT.schemas
    assert set(schemas["Capacite"]["enum"]) == {c.value for c in iam.Capacite}
    assert set(schemas["Decision"]["properties"]["decision"]["enum"]) == {
        v.value for v in iam.DecisionVerdict
    }
    assert set(schemas["Decision"]["properties"]["motif"]["enum"]) == {
        m.value for m in iam.DecisionMotif
    }


def test_every_cell_route_is_covered() -> None:
    missing = CONTRACT.missing_routes(
        [
            SDK_SOURCES / "cells" / "iam" / "cell.py",
        ]
    )
    assert not missing, "Routes IAM sans helper SDK :\n  " + "\n  ".join(missing)
