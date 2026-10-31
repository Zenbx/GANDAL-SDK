"""Helpers typés projects et vms : pages, modeles et suppression confirmee."""

from datetime import datetime, timezone

import respx

from gandal_sdk import GandalClient
from gandal_sdk.orchestration import (
    DeletionOut,
    DeletionPreviewOut,
    PowerAction,
    VMCreateRequestIn,
    VmState,
)


def _project(project_id: str = "prj-1") -> dict:
    return {
        "id": project_id,
        "name": "Alpha",
        "owner_id": "u1",
        "current_user_role": "owner",
        "created_at": "2026-01-01T00:00:00Z",
    }


def _vm(vm_id: str = "vm-1") -> dict:
    return {
        "id": vm_id,
        "origin_project_id": "prj-1",
        "name": "web-01",
        "ip_address": "10.0.0.1",
        "ram_gb": 8,
        "vcpu": 4,
        "vram_gb": 0,
        "ssd_gb": 80,
        "state": "stopped",
        "shared": False,
        "created_at": "2026-01-01T00:00:00Z",
    }


@respx.mock
def test_projects_list_returns_typed_page() -> None:
    """list() parse une Page[ProjectOut]."""
    respx.get("http://example.test/api/v1/projects").respond(
        200,
        json={
            "items": [_project()],
            "page": 1,
            "page_size": 20,
            "total_items": 1,
            "total_pages": 1,
        },
    )
    with GandalClient("http://example.test") as client:
        page = client.orchestration.projects.list()
        assert page.total_items == 1
        assert page.items[0].name == "Alpha"
        assert page.items[0].created_at == datetime(
            2026, 1, 1, tzinfo=timezone.utc
        )


@respx.mock
def test_vms_list_and_get_are_typed() -> None:
    """list/get renvoient VMOut avec enums."""
    respx.get("http://example.test/api/v1/projects/prj-1/vms").respond(
        200,
        json={
            "items": [_vm()],
            "page": 1,
            "page_size": 20,
            "total_items": 1,
            "total_pages": 1,
        },
    )
    respx.get("http://example.test/api/v1/projects/prj-1/vms/vm-1").respond(
        200, json=_vm()
    )
    with GandalClient("http://example.test") as client:
        page = client.orchestration.vms.list("prj-1", state=VmState.STOPPED)
        assert page.items[0].state is VmState.STOPPED
        vm = client.orchestration.vms.get("prj-1", "vm-1")
        assert vm.ram_gb == 8


@respx.mock
def test_vms_request_create_and_power() -> None:
    """request_create et power utilisent des schemas typés."""
    respx.post("http://example.test/api/v1/projects/prj-1/vms").respond(
        201,
        json={
            "id": "req-1",
            "project_id": "prj-1",
            "author_id": "u1",
            "kind": "vm_create",
            "status": "pending",
            "payload": {"name": "web-01"},
            "target_resource_type": None,
            "target_resource_id": None,
            "admin_note": None,
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
            "decided_at": None,
        },
    )
    respx.post("http://example.test/api/v1/projects/prj-1/vms/vm-1/power").respond(
        202,
        json={"vm_id": "vm-1", "action": "start", "state": "starting"},
    )
    with GandalClient("http://example.test") as client:
        req = client.orchestration.vms.request_create(
            "prj-1",
            VMCreateRequestIn(name="web-01", pack_id="pack-standard"),
        )
        assert req.status.value == "pending"
        power = client.orchestration.vms.power("prj-1", "vm-1", PowerAction.START)
        assert power.state.value == "starting"


@respx.mock
def test_vms_delete_preview_then_confirm() -> None:
    """delete sans confirm renvoie l'apercu ; confirm=True enchaine."""
    import httpx

    preview_body = {
        "confirmation_required": True,
        "confirmation_text": "SUPPRIMER web-01",
        "warning": "irreversible",
    }
    deleted_body = {
        "deleted": True,
        "resource_type": "vm",
        "resource_id": "vm-1",
        "message": "ok",
    }
    deletion = respx.post(
        "http://example.test/api/v1/projects/prj-1/vms/vm-1/deletion"
    )
    deletion.side_effect = [
        httpx.Response(200, json=preview_body),
        httpx.Response(200, json=deleted_body),
        httpx.Response(200, json=preview_body),
        httpx.Response(200, json=deleted_body),
    ]
    with GandalClient("http://example.test") as client:
        preview = client.orchestration.vms.delete("prj-1", "vm-1")
        assert isinstance(preview, DeletionPreviewOut)
        done = client.orchestration.vms.delete(
            "prj-1",
            "vm-1",
            confirmation_text=preview.confirmation_text,
        )
        assert isinstance(done, DeletionOut)
        auto = client.orchestration.vms.delete("prj-1", "vm-1", confirm=True)
        assert isinstance(auto, DeletionOut)
