"""Enumerations alignees sur le contrat de l'API d'orchestration."""

from enum import StrEnum


class RequestStatus(StrEnum):
    """Cycle de vie d'une demande."""

    PENDING = "pending"
    ACCEPTED = "accepted"
    REFUSED = "refused"
    CANCELLED = "cancelled"


class RequestKind(StrEnum):
    """Nature d'une demande."""

    VM_CREATE = "vm_create"
    VM_UPDATE = "vm_update"
    STORAGE_CREATE = "storage_create"
    STORAGE_UPDATE = "storage_update"


class ShareStatus(StrEnum):
    """Etat d'un partage."""

    ACTIVE = "active"
    REVOKED = "revoked"


class InvitationStatus(StrEnum):
    """Etat d'une invitation."""

    SENT = "sent"
    ACCEPTED = "accepted"
    REFUSED = "refused"
    CANCELLED = "cancelled"


class MembershipRole(StrEnum):
    """Role d'un membre dans un projet."""

    OWNER = "owner"
    GUEST = "guest"


class ResourceType(StrEnum):
    """Type de ressource partageable."""

    VM = "vm"
    STORAGE = "storage"


class VmState(StrEnum):
    """Etat local d'une VM."""

    PENDING = "pending"
    CREATING = "creating"
    STOPPED = "stopped"
    RUNNING = "running"
    DELETING = "deleting"
    ERROR = "error"
    UNKNOWN = "unknown"


class PowerState(StrEnum):
    """Etat transitoire apres une action d'alimentation."""

    STARTING = "starting"
    STOPPING = "stopping"
    RESTARTING = "restarting"


class StorageState(StrEnum):
    """Etat local d'un stockage."""

    AVAILABLE = "available"
    DELETING = "deleting"


class PowerAction(StrEnum):
    """Action d'alimentation directe."""

    START = "start"
    STOP = "stop"
    RESTART = "restart"
