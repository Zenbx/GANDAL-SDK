"""Attente qu'une ressource atteigne un etat (docs/CONVENTIONS_API.md §7).

Le moteur interroge la ressource a intervalle fixe jusqu'a un etat de succes,
un etat d'echec definitif, ou l'epuisement des tentatives. Les waiters concrets
(vms.wait_until_running, ...) ne font que lui fournir ces trois regles : quand
l'API exposera /operations, seul leur interieur changera.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

from gandal_sdk.errors import GandalApiError, GandalError

T = TypeVar("T")

DEFAULT_DELAY = 5.0
DEFAULT_MAX_ATTEMPTS = 60  # 5 minutes avec le delai par defaut

# Valeur renvoyee par wait_for quand la ressource a disparu (attente de suppression).
GONE = None


class WaiterError(GandalError):
    """La ressource n'a pas atteint l'etat attendu."""

    def __init__(self, message: str, *, last_value: object = None) -> None:
        """Conserve la derniere valeur lue pour le diagnostic de l'appelant."""
        super().__init__(message)
        self.last_value = last_value


class WaiterTimeout(WaiterError):
    """Tentatives epuisees sans etat final."""


class WaiterFailure(WaiterError):
    """La ressource a atteint un etat d'echec definitif : inutile d'attendre."""


def wait_for(
    fetch: Callable[[], T],
    *,
    is_success: Callable[[T], bool],
    failure_reason: Callable[[T], str | None] = lambda _: None,
    gone_is_success: bool = False,
    description: str,
    delay: float = DEFAULT_DELAY,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    sleep: Callable[[float], None],
) -> T | None:
    """Interroge fetch jusqu'au succes et renvoie la derniere valeur lue.

    failure_reason renvoie un message pour un etat d'echec definitif, None sinon.
    Avec gone_is_success, un 404 not_found termine l'attente et renvoie GONE.
    """
    if max_attempts < 1:
        raise ValueError("max_attempts doit valoir au moins 1")
    value: T | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            value = fetch()
        except GandalApiError as error:
            if gone_is_success and error.code == "not_found":
                return GONE
            raise
        if is_success(value):
            return value
        reason = failure_reason(value)
        if reason is not None:
            raise WaiterFailure(f"{description} : {reason}", last_value=value)
        if attempt < max_attempts:
            sleep(delay)
    raise WaiterTimeout(
        f"{description} : etat final non atteint apres {max_attempts} tentatives "
        f"espacees de {delay} s",
        last_value=value,
    )
