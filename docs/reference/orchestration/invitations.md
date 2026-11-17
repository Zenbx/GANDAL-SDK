# Invitations

Invitations recues par l'utilisateur courant.

**Acces :** `client.orchestration.invitations`

## `list`

```python
list(page: int, page_size: int, status: InvitationStatus | str | None) -> Page[InvitationOut]
```

Liste les invitations recues.

**Route :** `GET /api/v1/invitations`, `POST /api/v1/invitations/{invitation_id}/accept`, `POST /api/v1/invitations/{invitation_id}/refuse`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `accept`

```python
accept(invitation_id: str) -> InvitationOut
```

Accepte une invitation.

**Route :** `POST /api/v1/invitations/{invitation_id}/accept`, `POST /api/v1/invitations/{invitation_id}/refuse`, `POST /api/v1/invitations/{invitation_id}/cancel`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `refuse`

```python
refuse(invitation_id: str) -> InvitationOut
```

Refuse une invitation.

**Route :** `POST /api/v1/invitations/{invitation_id}/refuse`, `POST /api/v1/invitations/{invitation_id}/cancel`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `cancel`

```python
cancel(invitation_id: str) -> InvitationOut
```

Annule une invitation emise.

**Route :** `POST /api/v1/invitations/{invitation_id}/cancel`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.
