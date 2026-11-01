"""Relances automatiques du transport (docs/CONVENTIONS_API.md §5)."""

import httpx
import pytest
import respx

from gandal_sdk._http import HttpTransport, RetryPolicy
from gandal_sdk.errors import GandalApiError

UNAVAILABLE = {"error": {"code": "upstream_unavailable", "message": "panne", "details": None}}
THROTTLED = {"error": {"code": "throttled", "message": "trop vite", "details": None}}


def _transport(sleeps: list[float], attempts: int = 3) -> HttpTransport:
    """Transport dont les attentes sont enregistrees au lieu d'etre dormies."""
    return HttpTransport(
        "http://example.test",
        retry=RetryPolicy(max_attempts=attempts),
        sleep=sleeps.append,
    )


@respx.mock
def test_get_retries_503_then_succeeds() -> None:
    """Un GET rejoue un 503 et renvoie la reponse suivante."""
    route = respx.get("http://example.test/x").mock(
        side_effect=[httpx.Response(503, json=UNAVAILABLE), httpx.Response(200, json={"ok": 1})]
    )
    sleeps: list[float] = []
    assert _transport(sleeps).request("GET", "/x") == {"ok": 1}
    assert route.call_count == 2
    assert len(sleeps) == 1


@respx.mock
def test_gives_up_after_max_attempts() -> None:
    """Apres max_attempts, l'erreur de la derniere reponse remonte."""
    route = respx.get("http://example.test/x").respond(503, json=UNAVAILABLE)
    sleeps: list[float] = []
    with pytest.raises(GandalApiError) as caught:
        _transport(sleeps, attempts=3).request("GET", "/x")
    assert caught.value.code == "upstream_unavailable"
    assert route.call_count == 3
    assert len(sleeps) == 2


@respx.mock
def test_post_503_is_not_replayed() -> None:
    """Un POST sans cle d'idempotence n'est jamais rejoue sur 503 (risque de doublon)."""
    route = respx.post("http://example.test/x").respond(503, json=UNAVAILABLE)
    with pytest.raises(GandalApiError):
        _transport([]).request("POST", "/x", json={})
    assert route.call_count == 1


@respx.mock
def test_post_503_with_idempotency_key_is_replayed() -> None:
    """Avec Idempotency-Key, le POST devient rejouable."""
    route = respx.post("http://example.test/x").mock(
        side_effect=[httpx.Response(503, json=UNAVAILABLE), httpx.Response(201, json={"id": 1})]
    )
    result = _transport([]).request("POST", "/x", json={}, headers={"Idempotency-Key": "k-1"})
    assert result == {"id": 1}
    assert route.call_count == 2


@respx.mock
def test_post_429_is_replayed_with_retry_after() -> None:
    """Un 429 est rejoue meme en POST, apres le delai indique par Retry-After."""
    respx.post("http://example.test/x").mock(
        side_effect=[
            httpx.Response(429, json=THROTTLED, headers={"Retry-After": "2"}),
            httpx.Response(201, json={"id": 1}),
        ]
    )
    sleeps: list[float] = []
    assert _transport(sleeps).request("POST", "/x", json={}) == {"id": 1}
    assert sleeps == [2.0]


@respx.mock
def test_network_error_replayed_for_get_only() -> None:
    """Une erreur reseau est rejouee en GET, remontee telle quelle en POST."""
    get_route = respx.get("http://example.test/x").mock(
        side_effect=[httpx.ConnectError("refus"), httpx.Response(200, json={"ok": 1})]
    )
    assert _transport([]).request("GET", "/x") == {"ok": 1}
    assert get_route.call_count == 2

    post_route = respx.post("http://example.test/x").mock(side_effect=httpx.ConnectError("refus"))
    with pytest.raises(httpx.ConnectError):
        _transport([]).request("POST", "/x", json={})
    assert post_route.call_count == 1


@respx.mock
def test_other_4xx_are_never_replayed() -> None:
    """Un 409 ou 404 remonte immediatement."""
    route = respx.get("http://example.test/x").respond(
        404, json={"error": {"code": "not_found", "message": "absent", "details": None}}
    )
    with pytest.raises(GandalApiError):
        _transport([]).request("GET", "/x")
    assert route.call_count == 1


def test_backoff_is_bounded_and_grows() -> None:
    """L'attente exponentielle reste dans [plafond/2, plafond] et plafonne a max_delay."""
    policy = RetryPolicy(base_delay=1.0, max_delay=5.0)
    for attempt, ceiling in [(1, 1.0), (2, 2.0), (3, 4.0), (6, 5.0)]:
        assert ceiling / 2 <= policy.delay(attempt, None) <= ceiling
    assert policy.delay(1, "120") == 5.0
    assert 0.5 <= RetryPolicy(base_delay=1.0).delay(1, "Wed, 21 Oct 2026 07:28:00 GMT") <= 1.0
