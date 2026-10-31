"""Stub de la cellule Notifications (contrat aligne sur NotificationsPort)."""

from __future__ import annotations

from dataclasses import dataclass

from gandal_sdk.cells._base import not_ready


@dataclass(frozen=True)
class Notification:
    """Message destine a un utilisateur."""

    user_id: str
    subject: str
    message: str


class NotificationsCell:
    """Client de la cellule Notifications. Stub jusqu'a publication de son API."""

    def notify(self, notification: Notification) -> None:
        """Envoie une notification (pas encore disponible)."""
        not_ready("notifications")
