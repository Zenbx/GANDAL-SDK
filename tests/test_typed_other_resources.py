"""Helpers typés networks, packs, requests, shares, profiles, auth etelargie."""

import respx

from gandal_sdk import GandalClient
from gandal_sdk.orchestration.models import (
    PackCreateIn,
    ProfileCreateIn,
    UserUpdateIn,
)


@respx.mock
def test_networks_create_attach() -> None:
    """create et attach_vm renvoient NetworkOut."""
    network = {
        "id": "net-1",
        "project_id": "prj-1",
        "name": "lan",
        "vm_ids": [],
        "created_at": "2026-01-01T00:00:00Z",
    }
    respx.post("http://example.test/api/v1/projects/prj-1/networks").respond(
        201, json=network
    )
    attached = {**network, "vm_ids": ["vm-1"]}
    respx.post("http://example.test/api/v1/projects/prj-1/networks/net-1/vms").respond(
        200, json=attached
    )
    with GandalClient("http://example.test") as client:
        created = client.orchestration.networks.create("prj-1", "lan")
        assert created.name == "lan"
        result = client.orchestration.networks.attach_vm("prj-1", "net-1", "vm-1")
        assert result.vm_ids == ["vm-1"]


@respx.mock
def test_packs_admin_create() -> None:
    """create admin parse PackOut."""
    respx.post("http://example.test/api/v1/admin/packs").respond(
        201,
        json={
            "id": "pack-1",
            "name": "Standard",
            "description": "",
            "ram_gb": 8,
            "vcpu": 4,
            "vram_gb": 0,
            "ssd_gb": 80,
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
        },
    )
    with GandalClient("http://example.test") as client:
        pack = client.orchestration.packs.create(
            PackCreateIn(name="Standard", ram_gb=8, vcpu=4, vram_gb=0, ssd_gb=80)
        )
        assert pack.id == "pack-1"


@respx.mock
def test_requests_accept() -> None:
    """accept renvoie RequestOut."""
    body = {
        "id": "req-1",
        "project_id": "prj-1",
        "author_id": "u1",
        "kind": "vm_create",
        "status": "accepted",
        "payload": {},
        "target_resource_type": "vm",
        "target_resource_id": "vm-1",
        "admin_note": "ok",
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-01-01T00:00:00Z",
        "decided_at": "2026-01-01T01:00:00Z",
    }
    respx.post("http://example.test/api/v1/requests/req-1/accept").respond(200, json=body)
    with GandalClient("http://example.test") as client:
        req = client.orchestration.requests.accept("req-1", note="ok")
        assert req.status.value == "accepted"


@respx.mock
def test_shares_revoke() -> None:
    """revoke renvoie ShareRevokeOut."""
    respx.post("http://example.test/api/v1/shares/sh-1/revoke").respond(
        200,
        json={
            "share": {
                "id": "sh-1",
                "resource_type": "vm",
                "resource_id": "vm-1",
                "origin_project_id": "prj-1",
                "dest_project_id": "prj-2",
                "created_by": "u1",
                "status": "revoked",
                "created_at": "2026-01-01T00:00:00Z",
            },
            "message": "Le partage a ete revoque.",
        },
    )
    with GandalClient("http://example.test") as client:
        out = client.orchestration.shares.revoke("sh-1")
        assert out.share.status.value == "revoked"


@respx.mock
def test_profiles_list_rights_and_create() -> None:
    """list_rights et create profil."""
    respx.get("http://example.test/api/v1/admin/rights").respond(
        200,
        json=[{"code": "vm.view", "description": "Voir les VMs"}],
    )
    respx.post("http://example.test/api/v1/admin/profiles").respond(
        201,
        json={
            "id": "prof-1",
            "name": "Lecteur",
            "description": "",
            "rights": ["vm.view"],
        },
    )
    with GandalClient("http://example.test") as client:
        rights = client.orchestration.profiles.list_rights()
        assert rights[0].code == "vm.view"
        profile = client.orchestration.profiles.create(
            ProfileCreateIn(name="Lecteur", rights=["vm.view"])
        )
        assert profile.id == "prof-1"


@respx.mock
def test_auth_update_me_refreshes_token() -> None:
    """update_me stocke le nouveau Bearer."""
    respx.patch("http://example.test/api/v1/auth/me").respond(
        200,
        json={"access_token": "new-tok", "token_type": "bearer", "expires_in": 3600},
    )
    me = respx.get("http://example.test/api/v1/auth/me").respond(
        200,
        json={
            "user_id": "u1",
            "email": "new@iaas.cm",
            "first_name": "A",
            "last_name": "B",
            "role": "user",
        },
    )
    with GandalClient("http://example.test") as client:
        client.orchestration.auth.update_me(UserUpdateIn(email="new@iaas.cm"))
        client.orchestration.auth.me()
        assert me.calls[0].request.headers["Authorization"] == "Bearer new-tok"


@respx.mock
def test_orchestration_health_typed() -> None:
    """health() renvoie HealthOut."""
    respx.get("http://example.test/api/v1/health").respond(200, json={"status": "ok"})
    with GandalClient("http://example.test") as client:
        assert client.orchestration.health().status == "ok"


@respx.mock
def test_storages_list_typed() -> None:
    """list stockages parse StorageOut."""
    respx.get("http://example.test/api/v1/projects/prj-1/storages").respond(
        200,
        json={
            "items": [
                {
                    "id": "st-1",
                    "origin_project_id": "prj-1",
                    "name": "disk",
                    "ip_address": None,
                    "size_gb": 50,
                    "state": "available",
                    "shared": False,
                    "created_at": "2026-01-01T00:00:00Z",
                }
            ],
            "page": 1,
            "page_size": 20,
            "total_items": 1,
            "total_pages": 1,
        },
    )
    with GandalClient("http://example.test") as client:
        page = client.orchestration.storages.list("prj-1")
        assert page.items[0].size_gb == 50


@respx.mock
def test_invitations_accept() -> None:
    """accept invitation typée."""
    respx.post("http://example.test/api/v1/invitations/inv-1/accept").respond(
        200,
        json={
            "id": "inv-1",
            "project_id": "prj-1",
            "project_name": "Alpha",
            "inviter_id": "u1",
            "invitee_id": "u2",
            "invitee_email": "bob@iaas.cm",
            "status": "accepted",
            "profile_id": None,
            "additional_rights": [],
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
        },
    )
    with GandalClient("http://example.test") as client:
        inv = client.orchestration.invitations.accept("inv-1")
        assert inv.status.value == "accepted"
