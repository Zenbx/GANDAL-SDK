"""Moteur d'attente generique."""

import pytest

from gandal_sdk.errors import GandalApiError
from gandal_sdk.waiters import GONE, WaiterFailure, WaiterTimeout, wait_for


def _sequence(*values: object):
    """fetch qui renvoie les valeurs dans l'ordre (ou leve celles qui sont des exceptions)."""
    remaining = list(values)

    def fetch() -> object:
        value = remaining.pop(0)
        if isinstance(value, Exception):
            raise value
        return value

    return fetch


def test_returns_first_successful_value_and_sleeps_between_attempts() -> None:
    """Deux etats transitoires puis succes : deux attentes, valeur finale renvoyee."""
    sleeps: list[float] = []
    result = wait_for(
        _sequence("creating", "creating", "running"),
        is_success=lambda state: state == "running",
        description="VM vm-1",
        delay=2.0,
        sleep=sleeps.append,
    )
    assert result == "running"
    assert sleeps == [2.0, 2.0]


def test_failure_state_stops_immediately() -> None:
    """Un etat d'echec definitif leve WaiterFailure sans attendre le reste."""
    sleeps: list[float] = []
    with pytest.raises(WaiterFailure, match="VM vm-1 : etat error") as caught:
        wait_for(
            _sequence("creating", "error", "running"),
            is_success=lambda state: state == "running",
            failure_reason=lambda state: "etat error" if state == "error" else None,
            description="VM vm-1",
            sleep=sleeps.append,
        )
    assert caught.value.last_value == "error"
    assert len(sleeps) == 1


def test_timeout_after_max_attempts_without_trailing_sleep() -> None:
    """max_attempts lectures, max_attempts - 1 attentes, puis WaiterTimeout."""
    sleeps: list[float] = []
    with pytest.raises(WaiterTimeout) as caught:
        wait_for(
            _sequence("creating", "creating", "creating"),
            is_success=lambda state: state == "running",
            description="VM vm-1",
            max_attempts=3,
            sleep=sleeps.append,
        )
    assert caught.value.last_value == "creating"
    assert len(sleeps) == 2


def test_not_found_ends_deletion_wait() -> None:
    """Avec gone_is_success, un 404 not_found signifie : supprimee."""
    gone = GandalApiError("not_found", "absente", status=404)
    result = wait_for(
        _sequence("deleting", gone),
        is_success=lambda _: False,
        gone_is_success=True,
        description="VM vm-1",
        sleep=lambda _: None,
    )
    assert result is GONE


def test_other_api_errors_propagate() -> None:
    """Un 404 sans gone_is_success, ou un 403, remonte tel quel."""
    for error in (
        GandalApiError("not_found", "absente", status=404),
        GandalApiError("forbidden", "interdit", status=403),
    ):
        with pytest.raises(GandalApiError):
            wait_for(
                _sequence(error),
                is_success=lambda _: True,
                description="VM vm-1",
                sleep=lambda _: None,
            )


def test_rejects_zero_attempts() -> None:
    """max_attempts < 1 est une erreur de programmation."""
    with pytest.raises(ValueError):
        wait_for(lambda: 1, is_success=bool, description="x", max_attempts=0, sleep=print)
