# A - OIDC

Discovery OpenID et JWKS.

**Acces :** `client.iam`

!!! note
    Sans endpoint IAM configure, chaque appel leve `CellUnavailable`. Les ecritures envoient une `Idempotency-Key` (sauf `create_access_key` et `assume_role`). Erreurs en `application/problem+json` → `GandalApiError`.

## `openid_configuration`

```python
openid_configuration() -> dict[str, Any]
```

Document de discovery OIDC du fournisseur d'identite.

**Route :** `GET /.well-known/openid-configuration`, `GET /protocol/openid-connect/certs`, `POST /decisions`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `jwks`

```python
jwks() -> dict[str, Any]
```

Cles publiques JWKS pour verifier les jetons.

**Route :** `GET /protocol/openid-connect/certs`, `POST /decisions`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.
