"""Operations d'identite exposees par l'API d'orchestration."""

from __future__ import annotations

from pydantic import BaseModel, Field

from gandal_sdk._http import HttpTransport


class TokenOut(BaseModel):
    """Jeton renvoye par POST /api/v1/auth/login."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int


class IdentityOut(BaseModel):
    """Identite portee par le jeton courant."""

    user_id: str
    email: str
    first_name: str
    last_name: str
    role: str


class LoginIn(BaseModel):
    """Corps de connexion."""

    email: str = Field(min_length=3)
    password: str = Field(min_length=1)


class AuthApi:
    """Sous-client auth de l'orchestration (/api/v1/auth)."""

    def __init__(self, transport: HttpTransport) -> None:
        """Attache le transport HTTP partage."""
        self._http = transport

    def login(self, email: str, password: str) -> TokenOut:
        """Echange email/mot de passe contre un jeton Bearer."""
        payload = LoginIn(email=email, password=password)
        data = self._http.request("POST", "/api/v1/auth/login", json=payload.model_dump())
        return TokenOut.model_validate(data)

    def me(self) -> IdentityOut:
        """Lit l'identite associee au jeton courant."""
        data = self._http.request("GET", "/api/v1/auth/me")
        return IdentityOut.model_validate(data)
