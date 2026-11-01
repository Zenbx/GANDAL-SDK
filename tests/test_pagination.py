"""paginate parcourt toutes les pages d'une methode de liste."""

import httpx
import respx

from gandal_sdk import GandalClient, paginate
from gandal_sdk.orchestration.models import Page


def _vm(index: int) -> dict:
    """VM minimale au format VMOut."""
    return {
        "id": f"vm-{index}",
        "origin_project_id": "prj-1",
        "name": f"web-{index}",
        "ip_address": None,
        "ram_gb": 2,
        "vcpu": 1,
        "vram_gb": 0,
        "ssd_gb": 20,
        "state": "running",
        "created_at": "2026-01-01T00:00:00Z",
    }


def _page(items: list[dict], page: int, total_items: int, page_size: int = 2) -> dict:
    """Enveloppe de pagination de l'API."""
    return {
        "items": items,
        "page": page,
        "page_size": page_size,
        "total_items": total_items,
        "total_pages": -(-total_items // page_size),
    }


@respx.mock
def test_paginate_walks_every_page_and_forwards_filters() -> None:
    """Trois pages sont lues dans l'ordre, filtres et projet transmis a chaque appel."""
    pages = {
        "1": _page([_vm(1), _vm(2)], 1, 5),
        "2": _page([_vm(3), _vm(4)], 2, 5),
        "3": _page([_vm(5)], 3, 5),
    }
    route = respx.get("http://example.test/api/v1/projects/prj-1/vms").mock(
        side_effect=lambda request: httpx.Response(200, json=pages[request.url.params["page"]])
    )
    with GandalClient("http://example.test") as client:
        names = [
            vm.name
            for vm in paginate(client.orchestration.vms.list, "prj-1", page_size=2, state="running")
        ]
    assert names == ["web-1", "web-2", "web-3", "web-4", "web-5"]
    assert route.call_count == 3
    for call in route.calls:
        assert call.request.url.params["state"] == "running"
        assert call.request.url.params["page_size"] == "2"


def test_paginate_is_lazy() -> None:
    """Arreter la boucle ne demande pas les pages suivantes."""
    calls: list[int] = []

    def fake_list(*, page: int, page_size: int) -> Page[int]:
        calls.append(page)
        return Page[int](items=[page], page=page, page_size=1, total_items=9, total_pages=9)

    first = next(paginate(fake_list))
    assert first == 1
    assert calls == [1]


def test_paginate_handles_empty_and_shrinking_lists() -> None:
    """Liste vide : un seul appel. Page vide inattendue : arret sans boucle infinie."""
    empty = Page[int](items=[], page=1, page_size=100, total_items=0, total_pages=0)
    assert list(paginate(lambda **_: empty)) == []

    def shrinking(*, page: int, page_size: int) -> Page[int]:
        items = [1] if page == 1 else []
        return Page[int](items=items, page=page, page_size=1, total_items=3, total_pages=3)

    assert list(paginate(shrinking)) == [1]
