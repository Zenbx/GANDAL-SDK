"""Parcours de toutes les pages d'une liste (docs/CONVENTIONS_API.md §8)."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from typing import Any, TypeVar

from gandal_sdk.orchestration.models import Page

T = TypeVar("T")

# Maximum accepte par l'API (API_ENDPOINTS.md §1.3) : le moins d'allers-retours.
MAX_PAGE_SIZE = 100


def paginate(
    list_method: Callable[..., Page[T]],
    *args: Any,
    page_size: int = MAX_PAGE_SIZE,
    **filters: Any,
) -> Iterator[T]:
    """Itere sur les elements de toutes les pages d'une methode de liste du SDK.

    Les arguments positionnels et les filtres sont transmis tels quels :

        for vm in paginate(client.orchestration.vms.list, project_id, state=VmState.RUNNING):
            ...

    Les pages sont demandees a mesure : interrompre la boucle n'en charge pas davantage.
    """
    page_number = 1
    while True:
        page = list_method(*args, page=page_number, page_size=page_size, **filters)
        yield from page.items
        # items vide : garde-fou si total_pages change pendant le parcours.
        if page_number >= page.total_pages or not page.items:
            return
        page_number += 1
