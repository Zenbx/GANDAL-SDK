#!/usr/bin/env python3
"""Genere les pages de reference MkDocs a partir du code source du SDK.

Ne remplace pas les guides ni les recettes : uniquement reference/methode.
A relancer apres un changement de surface publique.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "gandal_sdk"
DOCS = ROOT / "docs" / "reference"

ROUTE_RE = re.compile(
    r'\._http\.request\(\s*"([A-Z]+)"\s*,\s*(?:f)?"([^"]+)"|'
    r'\._req\(\s*"([A-Z]+)"\s*,\s*(?:f)?"([^"]+)"|'
    r'self\._req\(\s*"([A-Z]+)"\s*,\s*(?:f)?"([^"]+)"'
)


def _doc_first(node: ast.AST) -> str:
    doc = ast.get_docstring(node) or ""
    lines = [ln.strip() for ln in doc.strip().splitlines() if ln.strip()]
    return " ".join(lines[:3]) if lines else ""


def _sig(fn: ast.FunctionDef) -> str:
    parts: list[str] = []
    args = fn.args
    pos = list(args.args)
    if pos and pos[0].arg == "self":
        pos = pos[1:]
    defaults = list(args.defaults)
    # Align defaults on the last N positional args
    default_offset = len(pos) - len(defaults)
    for i, a in enumerate(pos):
        ann = ast.unparse(a.annotation) if a.annotation else ""
        piece = f"{a.arg}: {ann}" if ann else a.arg
        if i >= default_offset:
            d = defaults[i - default_offset]
            piece += f" = {ast.unparse(d)}"
        parts.append(piece)
    for a in args.kwonlyargs:
        ann = ast.unparse(a.annotation) if a.annotation else ""
        piece = f"{a.arg}: {ann}" if ann else a.arg
        parts.append(piece)
    ret = ast.unparse(fn.returns) if fn.returns else "None"
    return f"{fn.name}({', '.join(parts)}) -> {ret}"


def _routes_near(source: str, lineno: int) -> list[str]:
    """Cherche METHOD + path dans les ~25 lignes suivant la def."""
    lines = source.splitlines()
    window = "\n".join(lines[lineno - 1 : lineno + 35])
    found: list[str] = []
    for m in re.finditer(
        r'request\(\s*"([A-Z]+)"\s*,\s*(?:f)?"([^"]+)"|'
        r'_req\(\s*"([A-Z]+)"\s*,\s*(?:f)?"([^"]+)"',
        window,
    ):
        method = m.group(1) or m.group(3)
        path = m.group(2) or m.group(4)
        found.append(f"`{method} {path}`")
    return found


def class_methods(path: Path, class_name: str) -> list[dict]:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    methods: list[dict] = []
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and not item.name.startswith("_"):
                    methods.append(
                        {
                            "name": item.name,
                            "sig": _sig(item),
                            "doc": _doc_first(item),
                            "routes": _routes_near(source, item.lineno),
                        }
                    )
    return methods


def write_method_page(
    title: str,
    intro: str,
    access: str,
    methods: list[dict],
    dest: Path,
    *,
    notes: str = "",
) -> None:
    lines = [
        f"# {title}",
        "",
        intro.strip(),
        "",
        f"**Acces :** `{access}`",
        "",
    ]
    if notes:
        lines.extend([notes.strip(), ""])
    for m in methods:
        lines.append(f"## `{m['name']}`")
        lines.append("")
        lines.append("```python")
        lines.append(m["sig"])
        lines.append("```")
        lines.append("")
        if m["doc"]:
            lines.append(m["doc"])
            lines.append("")
        if m["routes"]:
            lines.append("**Route :** " + ", ".join(m["routes"]))
            lines.append("")
        lines.append("**Exceptions :** `GandalApiError` sur erreur HTTP metier.")
        lines.append("")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print("wrote", dest.relative_to(ROOT))


def main() -> None:
    orch = SRC / "orchestration"
    mapping = [
        ("AuthApi", "Auth (orchestration)", "client.orchestration.auth",
         "Sous-client d'identite de l'API d'orchestration.",
         orch / "auth.py", DOCS / "orchestration" / "auth.md", ""),
        ("HealthApi", "Health (orchestration)", "client.orchestration.health",
         "Sondes de sante. `ready()` n'est pas sous `/api/v1`.",
         orch / "health.py", DOCS / "orchestration" / "health.md",
         "!!! tip\n    `OrchestrationApi.health()` appelle `check()`. "
         "Pour `ready()`, utiliser `client.orchestration.health.ready()`."),
        ("ProjectsApi", "Projects", "client.orchestration.projects",
         "Projets, membres et invitations emises depuis un projet.",
         orch / "projects.py", DOCS / "orchestration" / "projects.md",
         "!!! warning\n    `delete` est en deux temps (`confirm=False` apercu, "
         "`confirm=True` suppression)."),
        ("InvitationsApi", "Invitations", "client.orchestration.invitations",
         "Invitations recues par l'utilisateur courant.",
         orch / "invitations.py", DOCS / "orchestration" / "invitations.md", ""),
        ("VmsApi", "VMs", "client.orchestration.vms",
         "Machines virtuelles d'un projet : demandes, alimentation, partage, suppression.",
         orch / "vms.py", DOCS / "orchestration" / "vms.md",
         "!!! note\n    Creation et modification passent par une **demande** "
         "admin (`request_create` / `request_update`), pas un create direct."),
        ("StoragesApi", "Storages", "client.orchestration.storages",
         "Espaces de stockage projet.",
         orch / "storages.py", DOCS / "orchestration" / "storages.md",
         "!!! danger\n    Le backend a retire une partie de ces routes : "
         "certains helpers peuvent renvoyer 404."),
        ("NetworksApi", "Networks", "client.orchestration.networks",
         "Reseaux d'un projet et rattachement de VM.",
         orch / "networks.py", DOCS / "orchestration" / "networks.md", ""),
        ("PacksApi", "Packs", "client.orchestration.packs",
         "Catalogue de packs (lecture) et administration.",
         orch / "packs.py", DOCS / "orchestration" / "packs.md", ""),
        ("RequestsApi", "Requests", "client.orchestration.requests",
         "Moteur de demandes (creation / modification de ressources).",
         orch / "requests.py", DOCS / "orchestration" / "requests.md",
         "!!! warning\n    `RequestOut.id` est une **chaine** (UUID), pas un entier."),
        ("SharesApi", "Shares", "client.orchestration.shares",
         "Partages de ressources entre projets.",
         orch / "shares.py", DOCS / "orchestration" / "shares.md", ""),
        ("ProfilesApi", "Profiles", "client.orchestration.profiles",
         "Profils de droits et creation d'administrateurs.",
         orch / "profiles.py", DOCS / "orchestration" / "profiles.md",
         "!!! warning\n    `ProfileOut.id` et `profile_id` sont des **chaines**."),
    ]
    for class_name, title, access, intro, src, dest, notes in mapping:
        write_method_page(title, intro, access, class_methods(src, class_name), dest, notes=notes)

    # IAM families by method groups (order in cell.py)
    iam_src = SRC / "cells" / "iam" / "cell.py"
    iam_methods = class_methods(iam_src, "IamCell")
    families = {
        "a-oidc.md": ("A - OIDC", "Discovery OpenID et JWKS.",
                      ["openid_configuration", "jwks"]),
        "b-decisions.md": ("B - Decisions", "Autorisation simple et batch, catalogue d'actions.",
                           ["decide", "decide_batch", "list_actions"]),
        "c-sujets.md": ("C - Sujets, roles, audit", "Identites, quotas sujets, roles, journal.",
                        ["list_subjects", "create_subject", "get_me", "get_subject",
                         "deactivate_subject", "patch_subject_attributes",
                         "get_subject_quotas", "get_subject_roles", "set_subject_roles",
                         "list_audit"]),
        "d-projets.md": ("D - Projets et acces", "Projets IAM, membres, demandes d'acces.",
                         ["list_projects", "create_project", "get_project", "archive_project",
                          "list_members", "invite_member", "remove_member",
                          "change_member_capacity", "create_member", "transfer_project",
                          "list_access_requests", "request_access", "decide_access_request"]),
        "e-quotas.md": ("E - Quotas et reservations",
                        "Quotas, propositions, reservations, resize.",
                        ["get_my_quotas", "get_quota_aggregates", "publish_quota_capacity",
                         "list_quota_proposals", "propose_quota_plan", "decide_quota_proposal",
                         "reserve_quota", "get_reservation", "release_reservation",
                         "commit_reservation", "release_resource", "resize_resource"]),
        "f-machines.md": ("F - Machines, cles, STS, politiques",
                          "Identites machine, cles d'acces, assume_role, politiques.",
                          ["create_machine_identity", "list_access_keys", "create_access_key",
                           "delete_access_key", "set_access_key_status", "assume_role",
                           "revoke_session", "whoami", "list_assumable_roles",
                           "create_assumable_role", "get_assumable_role", "delete_assumable_role",
                           "attach_policy_to_role", "detach_policy_from_role",
                           "revoke_role_sessions", "list_policies", "create_policy",
                           "get_policy", "delete_policy", "attach_policy",
                           "detach_policy_organisation", "detach_policy",
                           "generate_base_policies", "simulate_policies",
                           "list_policy_context_keys"]),
        "g-ressources.md": ("G - Ressources et tags",
                            "Metadonnees de ressources comptees et tags.",
                            ["get_resource", "grant_resource_right", "revoke_resource_right",
                             "get_resource_quotas", "get_tags", "set_tags"]),
    }
    by_name = {m["name"]: m for m in iam_methods}
    for fname, (title, intro, names) in families.items():
        selected = [by_name[n] for n in names if n in by_name]
        notes = (
            "!!! note\n    Sans endpoint IAM configure, chaque appel leve "
            "`CellUnavailable`. Les ecritures envoient une `Idempotency-Key` "
            "(sauf `create_access_key` et `assume_role`). "
            "Erreurs en `application/problem+json` → `GandalApiError`."
        )
        write_method_page(
            title,
            intro,
            "client.iam",
            selected,
            DOCS / "iam" / fname,
            notes=notes,
        )

    hv = class_methods(SRC / "cells" / "hypervisor.py", "HypervisorCell")
    write_method_page(
        "Hyperviseur",
        "Pilotage des VM du pool via la cellule gandal-hypervisor.",
        "client.hypervisor",
        hv,
        DOCS / "hyperviseur.md",
        notes=(
            "!!! warning\n    Sans `cell_urls['hypervisor']` / "
            "`GANDAL_HYPERVISOR_ENDPOINT`, `CellUnavailable`."
        ),
    )

    net = class_methods(SRC / "cells" / "network" / "cell.py", "NetworkCell")
    write_method_page(
        "Reseau",
        "Agent reseau (executions /v1, check|apply). Contrat : agent_reseau "
        "docs/endpoints.",
        "client.network",
        net,
        DOCS / "reseau.md",
        notes=(
            "!!! warning\n    Sans `cell_urls['network']` / "
            "`GANDAL_NETWORK_ENDPOINT`, `CellUnavailable`.\n\n"
            "!!! note\n    Metier projet : `client.orchestration.networks`. "
            "Toujours `check` avant `apply`."
        ),
    )

    stub_parts = [
        "# Cellules encore en stub",
        "",
        "Ces cellules ne sont **pas** branchees. Chaque appel leve `CellUnavailable`.",
        "",
        "Ne pas confondre avec l'orchestration : `client.orchestration.networks` et "
        "`client.orchestration.storages` parlent a iaas-api. La cellule reseau est "
        "integree (`client.network`) ; stockage / DNS / notifications restent en stub.",
        "",
    ]
    for stub_file, class_name, title, access in [
        ("storage.py", "StorageCell", "Cellule stockage (stub)", "client.storage"),
        ("dns.py", "DnsCell", "Cellule DNS (stub)", "client.dns"),
        ("notifications.py", "NotificationsCell", "Cellule notifications (stub)",
         "client.notifications"),
    ]:
        methods = class_methods(SRC / "cells" / stub_file, class_name)
        stub_parts.append(f"## {title}")
        stub_parts.append("")
        stub_parts.append(f"**Acces :** `{access}`")
        stub_parts.append("")
        for m in methods:
            stub_parts.append(f"### `{m['name']}`")
            stub_parts.append("")
            stub_parts.append("```python")
            stub_parts.append(m["sig"])
            stub_parts.append("```")
            stub_parts.append("")
            if m["doc"]:
                stub_parts.append(m["doc"])
                stub_parts.append("")
            stub_parts.append("**Exceptions :** `CellUnavailable`.")
            stub_parts.append("")
    (DOCS / "cellules-stubs.md").write_text("\n".join(stub_parts), encoding="utf-8")
    print("wrote docs/reference/cellules-stubs.md")

    # Garde + AccesSsh
    write_method_page(
        "GardeIam",
        "Sequence decider → reserver → confirmer / liberer cote client. "
        "Ce n'est **pas** le controle d'acces autoritaire (celui-ci vit dans le backend).",
        "from gandal_sdk import GardeIam",
        class_methods(SRC / "garde.py", "GardeIam"),
        DOCS / "garde.md",
        notes="!!! danger\n    Contournable : appeler le backend directement ignore la garde.",
    )
    write_method_page(
        "AccesSsh",
        "Certificats SSH ephemeres via le signeur, puis ouverture de session.",
        "from gandal_sdk.acces_ssh import AccesSsh",
        class_methods(SRC / "acces_ssh.py", "AccesSsh"),
        DOCS / "acces-ssh.md",
        notes=(
            "!!! tip\n    CLI : `gandal-ssh`. Jetons : `GANDAL_JETON`, "
            "signeur : `GANDAL_SIGNEUR`, CA : `GANDAL_CA`."
        ),
    )


if __name__ == "__main__":
    main()
