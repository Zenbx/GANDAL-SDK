"""Operations d'identite exposees par l'API d'orchestration."""

from __future__ import annotations

from pydantic import BaseModel, Field

from gandal_sdk._http import HttpTransport
from gandal_sdk.orchestration.models import PasswordChangeIn, UserUpdateIn


class TokenOut(BaseModel):
    """Jeton renvoye par POST /api/v1/auth/login ou PATCH /auth/me."""

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
        data = self._http.request(
            "POST",
            "/api/v1/auth/login",
            json=payload.model_dump(),
        )
        token = TokenOut.model_validate(data)
        self._http.set_token(token.access_token)
        return token

    def me(self) -> IdentityOut:
        """Lit l'identite associee au jeton courant."""
        data = self._http.request("GET", "/api/v1/auth/me")
        return IdentityOut.model_validate(data)

    def update_me(self, body: UserUpdateIn) -> TokenOut:
        """Met a jour l'identite et conserve le nouveau jeton."""
        data = self._http.request(
            "PATCH",
            "/api/v1/auth/me",
            json=body.model_dump(exclude_none=True),
        )
        token = TokenOut.model_validate(data)
        self._http.set_token(token.access_token)
        return token

    def change_password(self, old_password: str, new_password: str) -> None:
        """Remplace le mot de passe apres verification de l'ancien."""
        body = PasswordChangeIn(old_password=old_password, new_password=new_password)
        self._http.request("POST", "/api/v1/auth/password", json=body.model_dump())

    def delete_me(self) -> None:
        """Supprime le compte courant."""
        self._http.request("DELETE", "/api/v1/auth/me")
        self._http.set_token(None)
