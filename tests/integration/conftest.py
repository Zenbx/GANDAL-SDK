"""Tests contre une vraie instance d'iaas-api (comptes de demonstration actives).

Ignores sauf si GANDAL_IT_ENDPOINT est defini, par exemple :

    GANDAL_IT_ENDPOINT=http://127.0.0.1:8765 pytest tests/integration
"""

from __future__ import annotations

import os
import uuid
from collections.abc import Iterator

import pytest

from gandal_sdk import GandalClient

ENDPOINT = os.environ.get("GANDAL_IT_ENDPOINT")

# Comptes crees par iaas-api avec IAM_SEED_DEMO_USERS=true.
ADMIN = ("admin@iaas.cm", "admin123")
ALICE = ("alice@iaas.cm", "alice123")


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Marque les tests du dossier et les ignore sans endpoint configure."""
    skip = pytest.mark.skip(reason="GANDAL_IT_ENDPOINT non defini")
    for item in items:
        if "tests/integration" in str(item.path).replace(os.sep, "/"):
            item.add_marker(pytest.mark.integration)
            if not ENDPOINT:
                item.add_marker(skip)


def _logged_in(credentials: tuple[str, str]) -> Iterator[GandalClient]:
    """Client authentifie, ferme a la fin du test."""
    assert ENDPOINT
    with GandalClient(ENDPOINT) as client:
        client.login(*credentials)
        yield client


@pytest.fixture
def anonymous() -> Iterator[GandalClient]:
    """Client sans jeton."""
    assert ENDPOINT
    with GandalClient(ENDPOINT) as client:
        yield client


@pytest.fixture
def admin() -> Iterator[GandalClient]:
    """Client connecte en administrateur."""
    yield from _logged_in(ADMIN)


@pytest.fixture
def alice() -> Iterator[GandalClient]:
    """Client connecte en utilisateur ordinaire."""
    yield from _logged_in(ALICE)


@pytest.fixture
def unique_name() -> str:
    """Nom unique : les tests restent rejouables sur une base deja utilisee."""
    return f"it-{uuid.uuid4().hex[:10]}"
