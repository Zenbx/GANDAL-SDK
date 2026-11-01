"""La version exposee par le paquet est celle declaree dans pyproject.toml."""

from importlib.metadata import version

import gandal_sdk


def test_version_matches_installed_metadata() -> None:
    """__version__ et les metadonnees d'installation ne divergent pas."""
    assert gandal_sdk.__version__ == version("gandal-sdk")
