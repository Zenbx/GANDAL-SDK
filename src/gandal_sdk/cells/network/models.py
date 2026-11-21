"""Modeles de la cellule Reseau (agent gandal_agent, branche refactor).

L'agent n'expose pas d'OpenAPI FastAPI : le contrat est une enveloppe
d'execution synchrone (docs/endpoints de agent_reseau) avec corps
schema_version / target_id / mode / action / spec.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class NetworkMode(StrEnum):
    """check calcule sans ecrire ; apply ecrit puis relit."""

    CHECK = "check"
    APPLY = "apply"


class ExecutionState(StrEnum):
    """Etat terminal (ou en cours) d'une execution agent."""

    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    UNKNOWN = "UNKNOWN"
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"


class NetworkRef(BaseModel):
    """Reference d'un reseau XCP-ng / agent (UUID ou cle metier selon l'action)."""

    network_id: str


class ExecutionResult(BaseModel):
    """Contenu de result dans l'enveloppe d'execution."""

    returncode: int | None = None
    data: Any = None
    code: str | None = None


class NetworkExecution(BaseModel):
    """Reponse synchrone d'un POST /v1/<domaine> ou GET /v1/executions/{id}."""

    execution_id: int
    operation: str | None = None
    state: ExecutionState | str
    result: ExecutionResult | dict[str, Any] | None = None
    replay: bool = False
    links: dict[str, str] = Field(default_factory=dict)

    @property
    def succeeded(self) -> bool:
        """Vrai si l'agent a termine avec succes."""
        return str(self.state) == ExecutionState.SUCCEEDED

    @property
    def data(self) -> Any:
        """Raccourci vers result.data (forme agent)."""
        if self.result is None:
            return None
        if isinstance(self.result, ExecutionResult):
            return self.result.data
        return self.result.get("data") if isinstance(self.result, dict) else None


class NetworkRequest(BaseModel):
    """Corps standard schema_version 1 des domaines reseau."""

    schema_version: int = 1
    target_id: str
    mode: NetworkMode | str = NetworkMode.CHECK
    action: str
    spec: dict[str, Any] = Field(default_factory=dict)
