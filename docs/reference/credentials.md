# Credentials

Module `gandal_sdk.credentials`.

## `Credentials`

Dataclass : `endpoint`, `token`, `hypervisor_endpoint`, `hypervisor_token`,
`iam_endpoint`, `iam_token`, `iam_ca`.

## `resolve_credentials`

```python
resolve_credentials(
    *,
    endpoint: str | None = None,
    token: str | None = None,
    profile: str | None = None,
    path: Path | None = None,
    environ: Mapping[str, str] | None = None,
) -> Credentials
```

Leve `GandalError` si aucun endpoint n'est resolu.

## `default_credentials_path`

`GANDAL_CREDENTIALS_FILE` ou `~/.gandal/credentials`.

Guide : [Identifiants](../guide/identifiants.md).
