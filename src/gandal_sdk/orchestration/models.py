"""Schemas typés miroir du contrat /api/v1 de l'orchestration."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Generic, Literal, TypeVar

from pydantic import BaseModel, Field, model_validator

from gandal_sdk.orchestration.enums import (
    InvitationStatus,
    MembershipRole,
    PowerAction,
    PowerState,
    RequestKind,
    RequestStatus,
    ResourceType,
    ShareStatus,
    StorageState,
    VmState,
)

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    """Page de resultats renvoyee par les listes de l'API."""

    items: list[T]
    page: int
    page_size: int
    total_items: int
    total_pages: int


class HealthOut(BaseModel):
    """Reponse de GET /api/v1/health."""

    status: str


class DeletionPreviewOut(BaseModel):
    """Phase 1 de suppression : texte a confirmer."""

    confirmation_required: Literal[True] = True
    confirmation_text: str
    warning: str


class DeletionOut(BaseModel):
    """Phase 2 de suppression : ressource effectivement supprimee."""

    deleted: Literal[True] = True
    resource_type: str
    resource_id: str
    message: str


class ProjectCreateIn(BaseModel):
    """Creation d'un projet."""

    name: str = Field(min_length=1, max_length=128)


class ProjectUpdateIn(BaseModel):
    """Renommage d'un projet."""

    name: str = Field(min_length=1, max_length=128)


class ProjectOut(BaseModel):
    """Projet tel que renvoye par l'API."""

    id: str
    name: str
    owner_id: str
    current_user_role: MembershipRole
    created_at: datetime


class ProjectMemberOut(BaseModel):
    """Membre d'un projet."""

    user_id: str
    role: MembershipRole
    profile_id: str | None
    rights: list[str]
    joined_at: datetime


class MemberRightsUpdateIn(BaseModel):
    """Modification des droits d'un invite."""

    profile_id: str | None = None
    additional_rights: list[str] | None = None


class InvitationCreateIn(BaseModel):
    """Invitation par email ou invitee_id."""

    invitee_id: str | None = None
    email: str | None = None
    profile_id: str | None = None
    additional_rights: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _one_identifier(self) -> InvitationCreateIn:
        if (self.invitee_id is None) == (self.email is None):
            raise ValueError("Fournir soit invitee_id, soit email, mais pas les deux.")
        return self


class InvitationOut(BaseModel):
    """Invitation et son etat."""

    id: str
    project_id: str
    project_name: str
    inviter_id: str
    invitee_id: str
    invitee_email: str | None
    status: InvitationStatus
    profile_id: str | None
    additional_rights: list[str]
    created_at: datetime
    updated_at: datetime


class VmConfigurationIn(BaseModel):
    """Configuration complete d'une VM."""

    ram_gb: int = Field(ge=1)
    vcpu: int = Field(ge=1)
    vram_gb: int = Field(ge=0)
    ssd_gb: int = Field(ge=1)


class VMCreateRequestIn(BaseModel):
    """Demande de creation de VM (pack ou configuration)."""

    name: str = Field(min_length=1, max_length=128)
    pack_id: str | None = None
    configuration: VmConfigurationIn | None = None

    @model_validator(mode="after")
    def _exactly_one(self) -> VMCreateRequestIn:
        if (self.pack_id is None) == (self.configuration is None):
            raise ValueError("Fournir exactement un des champs pack_id ou configuration.")
        return self


class VMUpdateRequestIn(BaseModel):
    """Demande de modification de VM."""

    configuration: VmConfigurationIn


class VMOut(BaseModel):
    """VM renvoyee par l'API."""

    id: str
    origin_project_id: str
    name: str
    ip_address: str | None
    ram_gb: int
    vcpu: int
    vram_gb: int
    ssd_gb: int
    state: VmState
    shared: bool = False
    created_at: datetime


class PowerOut(BaseModel):
    """Accuse d'une action d'alimentation."""

    vm_id: str
    action: PowerAction
    state: PowerState


class ConsoleOut(BaseModel):
    """Acces console temporaire."""

    url: str
    expires_in: int


class PackCreateIn(BaseModel):
    """Creation d'un pack (admin)."""

    name: str = Field(min_length=1, max_length=64)
    description: str = ""
    ram_gb: int = Field(ge=1)
    vcpu: int = Field(ge=1)
    vram_gb: int = Field(ge=0)
    ssd_gb: int = Field(ge=1)


class PackUpdateIn(BaseModel):
    """Modification partielle d'un pack."""

    name: str | None = None
    description: str | None = None
    ram_gb: int | None = Field(default=None, ge=1)
    vcpu: int | None = Field(default=None, ge=1)
    vram_gb: int | None = Field(default=None, ge=0)
    ssd_gb: int | None = Field(default=None, ge=1)


class PackOut(BaseModel):
    """Pack du catalogue."""

    id: str
    name: str
    description: str
    ram_gb: int
    vcpu: int
    vram_gb: int
    ssd_gb: int
    created_at: datetime
    updated_at: datetime


class NetworkCreateIn(BaseModel):
    """Creation d'un reseau."""

    name: str = Field(min_length=1, max_length=128)


class NetworkUpdateIn(BaseModel):
    """Renommage d'un reseau."""

    name: str = Field(min_length=1, max_length=128)


class NetworkOut(BaseModel):
    """Reseau et VMs rattachees."""

    id: str
    project_id: str
    name: str
    vm_ids: list[str] = Field(default_factory=list)
    created_at: datetime


class StorageCreateRequestIn(BaseModel):
    """Demande de creation de stockage."""

    name: str = Field(min_length=1, max_length=128)
    size_gb: int = Field(ge=1)


class StorageUpdateRequestIn(BaseModel):
    """Demande de redimensionnement."""

    size_gb: int = Field(ge=1)


class StorageOut(BaseModel):
    """Espace de stockage."""

    id: str
    origin_project_id: str
    name: str
    ip_address: str | None
    size_gb: int
    state: StorageState
    shared: bool = False
    created_at: datetime


class RequestDecisionIn(BaseModel):
    """Note optionnelle d'un administrateur."""

    note: str | None = None


class RequestOut(BaseModel):
    """Demande telle que renvoyee par l'API."""

    id: str
    project_id: str
    author_id: str
    kind: RequestKind
    status: RequestStatus
    payload: dict[str, Any]
    target_resource_type: str | None
    target_resource_id: str | None
    admin_note: str | None
    created_at: datetime
    updated_at: datetime
    decided_at: datetime | None


class ShareCreateIn(BaseModel):
    """Projet destinataire d'un partage."""

    dest_project_id: str


class ShareOut(BaseModel):
    """Partage tel que renvoye par l'API."""

    id: str
    resource_type: ResourceType
    resource_id: str
    origin_project_id: str
    dest_project_id: str
    created_by: str
    status: ShareStatus
    created_at: datetime


class ShareRevokeOut(BaseModel):
    """Reponse de revocation d'un partage."""

    share: ShareOut
    message: str


class RightOut(BaseModel):
    """Droit du catalogue."""

    code: str
    description: str


class ProfileOut(BaseModel):
    """Profil de droits."""

    id: str
    name: str
    description: str
    rights: list[str]


class ProfileCreateIn(BaseModel):
    """Creation d'un profil."""

    name: str = Field(min_length=1, max_length=64)
    description: str = ""
    rights: list[str] = Field(default_factory=list)


class ProfileUpdateIn(BaseModel):
    """Modification partielle d'un profil."""

    name: str | None = None
    description: str | None = None
    rights: list[str] | None = None


class UserUpdateIn(BaseModel):
    """Modification de l'identite courante."""

    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None


class PasswordChangeIn(BaseModel):
    """Changement de mot de passe."""

    old_password: str
    new_password: str = Field(min_length=6)
