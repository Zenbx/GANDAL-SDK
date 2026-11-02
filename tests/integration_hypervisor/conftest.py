"""Tests du SDK contre une vraie cellule gandal-hypervisor (faux pool ou pool reel).

Ignores sauf si GANDAL_IT_HYPERVISOR_ENDPOINT et GANDAL_IT_HYPERVISOR_TOKEN sont
definis ; scripts/run_hypervisor_integration.sh les fournit. Les VM creees sont
nommees sdk-it-* et toutes supprimees a la fin, meme en cas d'echec.
"""

from __future__ import annotations

import os
import uuid
from collections.abc import Iterator

import pytest

from gandal_sdk import GandalClient
from gandal_sdk.cells.hypervisor import HypervisorCell

ENDPOINT = os.environ.get("GANDAL_IT_HYPERVISOR_ENDPOINT")
TOKEN = os.environ.get("GANDAL_IT_HYPERVISOR_TOKEN")
# Pool reel : un clonage XOSTOR prend des minutes ; faux pool : quelques millisecondes.
DELAY = float(os.environ.get("GANDAL_IT_DELAY", "0.2"))
MAX_ATTEMPTS = int(os.environ.get("GANDAL_IT_MAX_ATTEMPTS", "300"))
# Faux pool : 10 Go. Pool reel (modele gandal-reference) : disque systeme plus grand.
SSD_GB = int(os.environ.get("GANDAL_IT_SSD_GB", "10"))
PREFIX = "sdk-it-"


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    skip = pytest.mark.skip(reason="GANDAL_IT_HYPERVISOR_ENDPOINT non defini")
    for item in items:
        if "tests/integration_hypervisor" in str(item.path).replace(os.sep, "/"):
            item.add_marker(pytest.mark.integration)
            if not (ENDPOINT and TOKEN):
                item.add_marker(skip)


@pytest.fixture(scope="session")
def cell() -> Iterator[HypervisorCell]:
    """Client de la cellule ; supprime en fin de session toute VM sdk-it-* restante."""
    assert ENDPOINT and TOKEN
    with GandalClient(
        "http://orchestration.inutilisee",
        cell_urls={"hypervisor": ENDPOINT},
        cell_tokens={"hypervisor": TOKEN},
    ) as client:
        yield client.hypervisor
        for vm in client.hypervisor.list_vms():
            if vm.name.startswith(PREFIX):
                try:
                    client.hypervisor.delete_vm(vm)
                    client.hypervisor.wait_until_deleted(vm, delay=DELAY, max_attempts=MAX_ATTEMPTS)
                except Exception as error:  # noqa: BLE001 - signaler sans masquer l'echec du test
                    print(f"NETTOYAGE IMPOSSIBLE de {vm.name} ({vm.vm_id}) : {error}")


@pytest.fixture
def vm_name() -> str:
    return f"{PREFIX}{uuid.uuid4().hex[:8]}"


WAIT = {"delay": DELAY, "max_attempts": MAX_ATTEMPTS}
