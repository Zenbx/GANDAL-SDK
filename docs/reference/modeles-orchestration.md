# Modeles orchestration

Import typique : `from gandal_sdk.orchestration import ...`

## Enums (`orchestration.enums`)

`RequestStatus`, `RequestKind`, `ShareStatus`, `InvitationStatus`, `MembershipRole`,
`ResourceType`, `VmState`, `PowerState`, `StorageState`, `PowerAction`.

## Pagine

`Page[T]` : `items`, `total` / champs de pagination aligns sur l'API.

## Identifiants

- `RequestOut.id` : **str** (UUID)
- `ProfileOut.id` : **str**
- `profile_id` partout : **str | None**

## Entrees frequentes

- `VMCreateRequestIn`, `VMUpdateRequestIn`, `VmConfigurationIn`
- `RegisterIn` (helpers register / create_admin ; routes absentes de l'OpenAPI actuel)
- `ReadinessOut` (`GET /ready`)
- `DeletionPreviewOut` / `DeletionOut` (suppression deux temps)

Auth : `TokenOut`, `IdentityOut`, `LoginIn` dans `orchestration.auth`.
