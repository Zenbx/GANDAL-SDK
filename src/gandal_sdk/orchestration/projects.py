"""Helpers typés pour les projets, membres et invitations de projet."""

from __future__ import annotations

from gandal_sdk._http import HttpTransport
from gandal_sdk.orchestration._util import delete_two_step, drop_none, parse_page
from gandal_sdk.orchestration.enums import InvitationStatus, MembershipRole
from gandal_sdk.orchestration.models import (
    DeletionOut,
    DeletionPreviewOut,
    InvitationCreateIn,
    InvitationOut,
    MemberRightsUpdateIn,
    Page,
    ProjectCreateIn,
    ProjectMemberOut,
    ProjectOut,
    ProjectUpdateIn,
)


class ProjectsApi:
    """Sous-client typé /api/v1/projects."""

    def __init__(self, transport: HttpTransport) -> None:
        """Attache le transport HTTP partage."""
        self._http = transport

    def list(self, *, page: int = 1, page_size: int = 20) -> Page[ProjectOut]:
        """Liste paginee des projets de l'appelant."""
        data = self._http.request(
            "GET",
            "/api/v1/projects",
            params={"page": page, "page_size": page_size},
        )
        return parse_page(data, ProjectOut)

    def get(self, project_id: str) -> ProjectOut:
        """Consulte un projet."""
        data = self._http.request("GET", f"/api/v1/projects/{project_id}")
        return ProjectOut.model_validate(data)

    def create(self, name: str) -> ProjectOut:
        """Cree un projet dont l'appelant devient proprietaire."""
        body = ProjectCreateIn(name=name)
        data = self._http.request("POST", "/api/v1/projects", json=body.model_dump())
        return ProjectOut.model_validate(data)

    def rename(self, project_id: str, name: str) -> ProjectOut:
        """Renomme un projet."""
        body = ProjectUpdateIn(name=name)
        data = self._http.request(
            "PATCH",
            f"/api/v1/projects/{project_id}",
            json=body.model_dump(),
        )
        return ProjectOut.model_validate(data)

    def delete(
        self,
        project_id: str,
        *,
        confirmation_text: str | None = None,
        confirm: bool = False,
    ) -> DeletionPreviewOut | DeletionOut:
        """Supprime un projet (protocole en deux temps)."""
        return delete_two_step(
            self._http,
            f"/api/v1/projects/{project_id}/deletion",
            confirmation_text=confirmation_text,
            confirm=confirm,
        )

    def list_members(
        self,
        project_id: str,
        *,
        page: int = 1,
        page_size: int = 20,
        role: MembershipRole | str | None = None,
    ) -> Page[ProjectMemberOut]:
        """Liste les membres d'un projet."""
        data = self._http.request(
            "GET",
            f"/api/v1/projects/{project_id}/members",
            params=drop_none(
                {"page": page, "page_size": page_size, "role": role}
            ),
        )
        return parse_page(data, ProjectMemberOut)

    def update_member_rights(
        self,
        project_id: str,
        user_id: str,
        body: MemberRightsUpdateIn,
    ) -> ProjectMemberOut:
        """Remplace le profil et/ou les droits additionnels d'un invite."""
        data = self._http.request(
            "PUT",
            f"/api/v1/projects/{project_id}/members/{user_id}/rights",
            json=body.model_dump(exclude_unset=True),
        )
        return ProjectMemberOut.model_validate(data)

    def remove_member(self, project_id: str, user_id: str) -> None:
        """Retire un invite du projet."""
        self._http.request(
            "DELETE",
            f"/api/v1/projects/{project_id}/members/{user_id}",
        )

    def create_invitation(
        self,
        project_id: str,
        body: InvitationCreateIn,
    ) -> InvitationOut:
        """Invite un utilisateur dans le projet."""
        data = self._http.request(
            "POST",
            f"/api/v1/projects/{project_id}/invitations",
            json=body.model_dump(exclude_none=True),
        )
        return InvitationOut.model_validate(data)

    def list_invitations(
        self,
        project_id: str,
        *,
        page: int = 1,
        page_size: int = 20,
        status: InvitationStatus | str | None = None,
        invitee_id: str | None = None,
    ) -> Page[InvitationOut]:
        """Liste les invitations d'un projet."""
        data = self._http.request(
            "GET",
            f"/api/v1/projects/{project_id}/invitations",
            params=drop_none(
                {
                    "page": page,
                    "page_size": page_size,
                    "status": status,
                    "invitee_id": invitee_id,
                }
            ),
        )
        return parse_page(data, InvitationOut)
