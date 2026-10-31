"""Cas nominaux et limites de GandalApiError / CellUnavailable."""

import pytest

from gandal_sdk.errors import CellUnavailable, GandalApiError


def test_gandal_api_error_exposes_fields() -> None:
    """Conserve code, message, details et statut."""
    err = GandalApiError("forbidden", "acces refuse", details={"x": 1}, status=403)
    assert err.code == "forbidden"
    assert err.message == "acces refuse"
    assert err.details == {"x": 1}
    assert err.status == 403
    assert "forbidden" in str(err)


def test_cell_unavailable_names_the_cell() -> None:
    """Indique clairement quelle cellule manque."""
    err = CellUnavailable("hypervisor")
    assert err.cell_name == "hypervisor"
    assert "hypervisor" in str(err)


def test_cell_unavailable_is_gandal_error() -> None:
    """CellUnavailable reste dans la hierarchie GandalError."""
    from gandal_sdk.errors import GandalError

    with pytest.raises(GandalError):
        raise CellUnavailable("dns")
