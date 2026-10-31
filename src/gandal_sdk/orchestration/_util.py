"""Utilitaires internes des helpers typés."""

from __future__ import annotations

from typing import Any, TypeVar

from pydantic import BaseModel, TypeAdapter

from gandal_sdk._http import HttpTransport
from gandal_sdk.orchestration.models import DeletionOut, DeletionPreviewOut, Page

T = TypeVar("T", bound=BaseModel)


def drop_none(params: dict[str, Any]) -> dict[str, Any]:
    """Retire les cles a valeur None des query params."""
    return {key: value for key, value in params.items() if value is not None}


def parse_page(data: Any, item_type: type[T]) -> Page[T]:
    """Parse une page JSON en Page[item_type]."""
    adapter = TypeAdapter(Page[item_type])
    return adapter.validate_python(data)


def parse_deletion(data: Any) -> DeletionPreviewOut | DeletionOut:
    """Discerne apercu et confirmation de suppression."""
    if isinstance(data, dict) and data.get("deleted") is True:
        return DeletionOut.model_validate(data)
    return DeletionPreviewOut.model_validate(data)


def delete_two_step(
    http: HttpTransport,
    path: str,
    *,
    confirmation_text: str | None = None,
    confirm: bool = False,
) -> DeletionPreviewOut | DeletionOut:
    """Execute le protocole de suppression en deux temps.

    - sans confirmation_text et confirm=False : renvoie l'apercu
    - avec confirmation_text : confirme la suppression
    - avec confirm=True : enchaine apercu puis confirmation automatiquement
    """
    if confirm and confirmation_text is None:
        preview = parse_deletion(http.request("POST", path, json={}))
        if not isinstance(preview, DeletionPreviewOut):
            return preview
        confirmation_text = preview.confirmation_text
    body = (
        {}
        if confirmation_text is None
        else {"confirmation_text": confirmation_text}
    )
    return parse_deletion(http.request("POST", path, json=body))
