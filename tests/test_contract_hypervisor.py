"""Compatibilite du client hyperviseur avec l'instantane openapi/gandal-hypervisor.json."""

from __future__ import annotations

import pytest
from contract import SDK_SOURCES, OpenApiContract

from gandal_sdk.cells import hypervisor

CONTRACT = OpenApiContract("gandal-hypervisor.json")

# (modele du SDK, schema de la cellule, sens) ; "out" = le SDK lit, "in" = le SDK envoie.
MODEL_PAIRS: list[tuple[type, str, str]] = [
    (hypervisor.VmSpec, "VmSpec", "in"),
    (hypervisor.HypervisorVm, "VmView", "out"),
    (hypervisor.CellOperation, "Operation", "out"),
    (hypervisor.CellError, "ErrorInfo", "out"),
    (hypervisor.CreatedVm, "CreatedOut", "out"),
]


@pytest.mark.parametrize(
    ("sdk_model", "schema_name", "direction"),
    MODEL_PAIRS,
    ids=[name for _, name, _ in MODEL_PAIRS],
)
def test_model_matches_schema(sdk_model: type, schema_name: str, direction: str) -> None:
    problems = CONTRACT.model_problems(sdk_model, schema_name, direction)
    assert not problems, f"{sdk_model.__name__} <> {schema_name} :\n  " + "\n  ".join(problems)


def test_states_and_statuses_match() -> None:
    """Les enumerations du SDK couvrent toutes les valeurs que la cellule peut renvoyer."""
    schemas = CONTRACT.schemas
    assert set(schemas["VmState"]["enum"]) <= {s.value for s in hypervisor.VmState}
    assert set(schemas["OperationStatus"]["enum"]) == {s.value for s in hypervisor.OperationStatus}
    assert set(schemas["PowerAction"]["enum"]) == {a.value for a in hypervisor.PowerAction}


def test_every_cell_route_is_covered() -> None:
    missing = CONTRACT.missing_routes([SDK_SOURCES / "cells" / "hypervisor.py"])
    assert not missing, "Routes de la cellule sans helper SDK :\n  " + "\n  ".join(missing)
