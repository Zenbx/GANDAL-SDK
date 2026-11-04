"""Transport HTTP : succes, 204 et mapping d'erreurs API."""

import httpx
import pytest
import respx

from gandal_sdk._http import HttpTransport, RetryPolicy
from gandal_sdk.errors import GandalApiError


@respx.mock
def test_request_returns_json_on_success() -> None:
    """Un 200 JSON est renvoye tel quel."""
    respx.get("http://example.test/api/v1/health").respond(200, json={"status": "ok"})
    transport = HttpTransport("http://example.test")
    try:
        assert transport.request("GET", "/api/v1/health") == {"status": "ok"}
    finally:
        transport.close()


@respx.mock
def test_request_returns_none_on_204() -> None:
    """Un 204 sans corps donne None."""
    respx.delete("http://example.test/api/v1/x").respond(204)
    transport = HttpTransport("http://example.test")
    try:
        assert transport.request("DELETE", "/api/v1/x") is None
    finally:
        transport.close()


@respx.mock
def test_request_maps_api_error_envelope() -> None:
    """Le format {error: {...}} devient GandalApiError."""
    respx.get("http://example.test/api/v1/x").respond(
        404,
        json={"error": {"code": "not_found", "message": "absent", "details": None}},
    )
    transport = HttpTransport("http://example.test")
    try:
        with pytest.raises(GandalApiError) as caught:
            transport.request("GET", "/api/v1/x")
        assert caught.value.code == "not_found"
        assert caught.value.status == 404
    finally:
        transport.close()


@respx.mock
def test_request_sends_bearer_when_set() -> None:
    """Le jeton est injecte dans Authorization."""
    route = respx.get("http://example.test/api/v1/auth/me").respond(
        200, json={"user_id": "u1", "email": "a@b.c", "first_name": "A", "last_name": "B", "role": "user"}
    )
    transport = HttpTransport("http://example.test")
    transport.set_token("tok-123")
    try:
        transport.request("GET", "/api/v1/auth/me")
        assert route.calls[0].request.headers["Authorization"] == "Bearer tok-123"
    finally:
        transport.close()


@respx.mock
def test_request_raises_on_non_json_error() -> None:
    """Une erreur non JSON reste une GandalApiError."""
    respx.get("http://example.test/boom").respond(500, text="down")
    transport = HttpTransport("http://example.test")
    try:
        with pytest.raises(GandalApiError) as caught:
            transport.request("GET", "/boom")
        assert caught.value.status == 500
    finally:
        transport.close()


def test_close_is_safe_with_injected_client() -> None:
    """close() ne ferme pas un client httpx injecte."""
    client = httpx.Client(base_url="http://example.test")
    transport = HttpTransport("http://example.test", client=client)
    transport.close()
    # le client injecte reste utilisable
    client.close()


# Reponses relevees telles quelles sur iaas-api (FastAPI par defaut, sans enveloppe).
@pytest.mark.parametrize(
    ("status", "body", "code", "message"),
    [
        (401, {"detail": "Jeton manquant"}, "unauthorized", "Jeton manquant"),
        (403, {"detail": "Réservé aux administrateurs"}, "forbidden", "Réservé aux administrateurs"),
        (404, {"detail": "Not Found"}, "not_found", "Not Found"),
        (500, {"detail": "boom"}, "internal_error", "boom"),
    ],
)
@respx.mock
def test_fastapi_detail_errors_get_code_from_status(
    status: int, body: dict, code: str, message: str
) -> None:
    """Sans enveloppe {error}, le code vient du statut HTTP et le message de detail."""
    respx.get("http://example.test/x").respond(status, json=body)
    transport = HttpTransport("http://example.test", retry=RetryPolicy(max_attempts=1))
    with pytest.raises(GandalApiError) as caught:
        transport.request("GET", "/x")
    assert (caught.value.code, caught.value.message) == (code, message)
    assert caught.value.details is None


@respx.mock
def test_problem_json_rfc9457() -> None:
    """Une erreur application/problem+json (IAM) devient GandalApiError."""
    respx.get("http://example.test/x").respond(
        403,
        headers={"content-type": "application/problem+json"},
        json={
            "type": "https://gandal.local/problems/interdit",
            "title": "Interdit",
            "status": 403,
            "detail": "capacite insuffisante",
            "correlation_id": "01JB9X2K7M4Q8V0ZC3N5T6R7W8",
        },
    )
    transport = HttpTransport("http://example.test", retry=RetryPolicy(max_attempts=1))
    with pytest.raises(GandalApiError) as caught:
        transport.request("GET", "/x")
    assert caught.value.code == "interdit"
    assert caught.value.message == "capacite insuffisante"
    assert caught.value.details["title"] == "Interdit"


@respx.mock
def test_fastapi_validation_errors_kept_in_details() -> None:
    """Un 422 de FastAPI garde la liste des champs fautifs dans details."""
    errors = [
        {
            "type": "less_than_equal",
            "loc": ["query", "page_size"],
            "msg": "Input should be less than or equal to 100",
        }
    ]
    respx.get("http://example.test/x").respond(422, json={"detail": errors})
    transport = HttpTransport("http://example.test")
    with pytest.raises(GandalApiError) as caught:
        transport.request("GET", "/x")
    assert caught.value.code == "validation_error"
    assert caught.value.details == errors
