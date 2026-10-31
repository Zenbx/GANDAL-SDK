"""Stub de la cellule IAM (contrat aligne sur IamPort)."""

from __future__ import annotations

from collections.abc import Collection
from dataclasses import dataclass
from enum import StrEnum

from gandal_sdk.cells._base import not_ready


class GlobalRole(StrEnum):
    """Role global porte par l'identite IAM."""

    USER = "user"
    ADMIN = "admin"


@dataclass(frozen=True)
class Identity:
    """Identite lue dans un jeton valide."""

    user_id: str
    email: str
    first_name: str
    last_name: str
    role: GlobalRole


@dataclass(frozen=True)
class AuthToken:
    """Jeton d'acces IAM."""

    access_token: str
    expires_in: int
    token_type: str = "bearer"


@dataclass(frozen=True)
class MemberGrant:
    """Membre d'un projet avec ses droits."""

    user_id: str
    is_owner: bool
    rights: frozenset[str]


class IamCell:
    """Client de la cellule IAM. Stub jusqu'a publication de son API."""

    def login(self, email: str, password: str) -> AuthToken:
        """Connexion IAM directe (pas encore disponible)."""
        not_ready("iam")

    def validate_token(self, token: str) -> Identity:
        """Validation d'un jeton IAM (pas encore disponible)."""
        not_ready("iam")

    def get_user(self, user_id: str) -> Identity:
        """Lecture d'un utilisateur (pas encore disponible)."""
        not_ready("iam")

    def get_rights(self, user_id: str, project_id: str) -> frozenset[str]:
        """Droits d'un utilisateur sur un projet (pas encore disponible)."""
        not_ready("iam")

    def list_projects(self, user_id: str) -> frozenset[str]:
        """Projets accessibles a un utilisateur (pas encore disponible)."""
        not_ready("iam")

    def list_members(self, project_id: str) -> tuple[MemberGrant, ...]:
        """Membres d'un projet (pas encore disponible)."""
        not_ready("iam")

    def invite_user(self, user_id: str, project_id: str, rights: Collection[str]) -> None:
        """Invitation d'un membre (pas encore disponible)."""
        not_ready("iam")
