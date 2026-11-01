"""Authentification contre la vraie iaas-api."""

import pytest

from gandal_sdk import GandalApiError, GandalClient
from gandal_sdk.orchestration.models import UserUpdateIn

from .conftest import ADMIN, ALICE, ENDPOINT


def test_login_then_me(anonymous: GandalClient) -> None:
    """Le jeton obtenu au login identifie l'utilisateur."""
    token = anonymous.login(*ALICE)
    assert token.token_type == "bearer"
    assert token.expires_in > 0
    me = anonymous.me()
    assert (me.email, me.role) == (ALICE[0], "user")


def test_admin_role(admin: GandalClient) -> None:
    """Le compte administrateur porte le role admin."""
    assert admin.me().role == "admin"


def test_wrong_password_is_unauthorized(anonymous: GandalClient) -> None:
    """Mauvais mot de passe : unauthorized, sans jeton conserve."""
    with pytest.raises(GandalApiError) as caught:
        anonymous.login(ADMIN[0], "mauvais-mot-de-passe")
    assert (caught.value.status, caught.value.code) == (401, "unauthorized")
    assert anonymous._http.token is None


def test_missing_token_is_unauthorized(anonymous: GandalClient) -> None:
    """Sans jeton, /auth/me est refuse."""
    with pytest.raises(GandalApiError) as caught:
        anonymous.me()
    assert caught.value.code == "unauthorized"


def test_update_me_switches_to_new_token(alice: GandalClient) -> None:
    """update_me renvoie un nouveau jeton, que le client utilise aussitot."""
    before = alice._http.token
    original = alice.me().first_name
    try:
        alice.orchestration.auth.update_me(UserUpdateIn(first_name="Alice-IT"))
        assert alice.me().first_name == "Alice-IT"
        assert alice._http.token != before
    finally:
        alice.orchestration.auth.update_me(UserUpdateIn(first_name=original))


def test_change_password_round_trip() -> None:
    """Le nouveau mot de passe permet de se connecter ; l'ancien est restaure."""
    assert ENDPOINT
    with GandalClient(ENDPOINT) as client:
        client.login(*ALICE)
        client.orchestration.auth.change_password(ALICE[1], "alice-it-provisoire")
        try:
            with GandalClient(ENDPOINT) as other:
                other.login(ALICE[0], "alice-it-provisoire")
        finally:
            client.orchestration.auth.change_password("alice-it-provisoire", ALICE[1])
