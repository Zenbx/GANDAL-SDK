"""Profils de droits contre la vraie iaas-api."""

import pytest

from gandal_sdk import GandalApiError, GandalClient, paginate
from gandal_sdk.orchestration.models import ProfileCreateIn, ProfileUpdateIn


def test_rights_catalog_is_seeded(alice: GandalClient) -> None:
    """Le catalogue de droits est lisible par tout utilisateur connecte."""
    codes = {right.code for right in alice.orchestration.profiles.list_rights()}
    assert "vm.view" in codes


def test_profile_lifecycle(admin: GandalClient, unique_name: str) -> None:
    """Creation, lecture paginee, modification, suppression ; id entier de bout en bout."""
    profiles = admin.orchestration.profiles
    created = profiles.create(ProfileCreateIn(name=unique_name, rights=["vm.view"]))
    try:
        assert isinstance(created.id, int)
        listed = {p.id: p for p in paginate(profiles.list, page_size=1)}
        assert listed[created.id].rights == ["vm.view"]

        updated = profiles.update(created.id, ProfileUpdateIn(description="mise a jour"))
        assert (updated.name, updated.description) == (unique_name, "mise a jour")
    finally:
        profiles.delete(created.id)

    with pytest.raises(GandalApiError) as caught:
        profiles.delete(created.id)
    assert caught.value.code == "not_found"


def test_duplicate_name_is_conflict(admin: GandalClient, unique_name: str) -> None:
    """Deux profils du meme nom : 409 conflict."""
    profiles = admin.orchestration.profiles
    created = profiles.create(ProfileCreateIn(name=unique_name))
    try:
        with pytest.raises(GandalApiError) as caught:
            profiles.create(ProfileCreateIn(name=unique_name))
        assert caught.value.code == "conflict"
    finally:
        profiles.delete(created.id)


def test_unknown_right_is_validation_error(admin: GandalClient, unique_name: str) -> None:
    """Un code de droit inexistant est refuse avec un message explicite."""
    with pytest.raises(GandalApiError) as caught:
        admin.orchestration.profiles.create(
            ProfileCreateIn(name=unique_name, rights=["nexiste.pas"])
        )
    assert caught.value.code == "validation_error"
    assert "nexiste.pas" in caught.value.message


def test_page_size_above_limit_reports_field(admin: GandalClient) -> None:
    """page_size > 100 : validation_error avec le champ fautif dans details."""
    with pytest.raises(GandalApiError) as caught:
        admin.orchestration.profiles.list(page_size=500)
    assert caught.value.code == "validation_error"
    assert caught.value.details[0]["loc"] == ["query", "page_size"]


def test_regular_user_cannot_write_profiles(alice: GandalClient, unique_name: str) -> None:
    """Un utilisateur peut lire les profils mais pas en creer."""
    alice.orchestration.profiles.list()
    with pytest.raises(GandalApiError) as caught:
        alice.orchestration.profiles.create(ProfileCreateIn(name=unique_name))
    assert caught.value.code == "forbidden"
