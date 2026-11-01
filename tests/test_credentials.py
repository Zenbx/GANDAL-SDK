"""Chaine de resolution de l'endpoint et du jeton."""

from pathlib import Path

import pytest
import respx

from gandal_sdk import GandalClient, GandalError
from gandal_sdk.credentials import Credentials, resolve_credentials

FILE = """
[default]
endpoint = http://fichier-default.test
token = jeton-fichier-default

[admin]
endpoint = http://fichier-admin.test
token = jeton-fichier-admin
"""


@pytest.fixture
def creds_file(tmp_path: Path) -> Path:
    """Fichier d'identifiants a deux profils."""
    path = tmp_path / "credentials"
    path.write_text(FILE)
    return path


def test_explicit_beats_env_beats_file(creds_file: Path) -> None:
    """Chaque champ suit l'ordre explicite > environnement > fichier."""
    env = {"GANDAL_ENDPOINT": "http://env.test"}
    assert resolve_credentials(path=creds_file, environ=env) == Credentials(
        "http://env.test", "jeton-fichier-default"
    )
    explicit = resolve_credentials(
        endpoint="http://explicite.test", token="jeton-explicite", path=creds_file, environ=env
    )
    assert explicit == Credentials("http://explicite.test", "jeton-explicite")


def test_profile_from_argument_or_env(creds_file: Path) -> None:
    """Le profil vient de l'argument, sinon de GANDAL_PROFILE."""
    by_arg = resolve_credentials(profile="admin", path=creds_file, environ={})
    assert by_arg.endpoint == "http://fichier-admin.test"
    by_env = resolve_credentials(path=creds_file, environ={"GANDAL_PROFILE": "admin"})
    assert by_env.token == "jeton-fichier-admin"


def test_named_profile_must_exist(creds_file: Path, tmp_path: Path) -> None:
    """Un profil demande mais introuvable est une erreur, pas un repli silencieux."""
    with pytest.raises(GandalError, match="absent"):
        resolve_credentials(profile="inconnu", path=creds_file, environ={})
    with pytest.raises(GandalError, match="introuvable"):
        resolve_credentials(profile="admin", path=tmp_path / "absent", environ={})


def test_env_only_without_file(tmp_path: Path) -> None:
    """Sans fichier, l'environnement suffit ; le jeton est facultatif."""
    creds = resolve_credentials(
        path=tmp_path / "absent", environ={"GANDAL_ENDPOINT": "http://env.test"}
    )
    assert creds == Credentials("http://env.test", None)


def test_missing_endpoint_is_explained(tmp_path: Path) -> None:
    """Aucune source d'endpoint : message qui dit comment en fournir une."""
    with pytest.raises(GandalError, match="GANDAL_ENDPOINT"):
        resolve_credentials(path=tmp_path / "absent", environ={})


def test_credentials_file_env_override(creds_file: Path) -> None:
    """GANDAL_CREDENTIALS_FILE designe un autre fichier."""
    creds = resolve_credentials(environ={"GANDAL_CREDENTIALS_FILE": str(creds_file)})
    assert creds.endpoint == "http://fichier-default.test"


def test_token_never_in_repr() -> None:
    """Le jeton n'apparait pas dans repr, donc ni dans les journaux ni les traces."""
    assert "secret" not in repr(Credentials("http://x.test", "secret"))


@respx.mock
def test_from_env_sends_resolved_token(creds_file: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """from_env pointe sur l'endpoint du profil et envoie son jeton."""
    monkeypatch.setenv("GANDAL_CREDENTIALS_FILE", str(creds_file))
    monkeypatch.delenv("GANDAL_ENDPOINT", raising=False)
    monkeypatch.delenv("GANDAL_TOKEN", raising=False)
    monkeypatch.delenv("GANDAL_PROFILE", raising=False)
    route = respx.get("http://fichier-admin.test/api/v1/health").respond(200, json={"status": "ok"})
    with GandalClient.from_env(profile="admin") as client:
        client.orchestration.health()
    assert route.calls.last.request.headers["Authorization"] == "Bearer jeton-fichier-admin"


@respx.mock
def test_from_env_configures_hypervisor_cell(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """L'endpoint et le jeton de la cellule viennent du profil ; l'env les remplace."""
    path = tmp_path / "credentials"
    path.write_text(
        "[default]\nendpoint = http://api.test\n"
        "hypervisor_endpoint = http://cell-fichier.test\nhypervisor_token = jeton-fichier\n"
    )
    monkeypatch.setenv("GANDAL_CREDENTIALS_FILE", str(path))
    for name in ("GANDAL_ENDPOINT", "GANDAL_TOKEN", "GANDAL_PROFILE", "GANDAL_HYPERVISOR_ENDPOINT"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("GANDAL_HYPERVISOR_TOKEN", "jeton-env")
    route = respx.get("http://cell-fichier.test/v1/vms").respond(200, json={"items": []})
    with GandalClient.from_env() as client:
        assert client.hypervisor.list_vms() == []
    assert route.calls.last.request.headers["Authorization"] == "Bearer jeton-env"
    assert "jeton" not in repr(resolve_credentials(path=path, environ={}))
