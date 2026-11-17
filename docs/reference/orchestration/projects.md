# Projects

Projets, membres et invitations emises depuis un projet.

**Acces :** `client.orchestration.projects`

!!! warning
    `delete` est en deux temps (`confirm=False` apercu, `confirm=True` suppression).

## `list`

```python
list(page: int, page_size: int) -> Page[ProjectOut]
```

Liste paginee des projets de l'appelant.

**Route :** `GET /api/v1/projects`, `GET /api/v1/projects/{project_id}`, `POST /api/v1/projects`, `PATCH /api/v1/projects/{project_id}`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `get`

```python
get(project_id: str) -> ProjectOut
```

Consulte un projet.

**Route :** `GET /api/v1/projects/{project_id}`, `POST /api/v1/projects`, `PATCH /api/v1/projects/{project_id}`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `create`

```python
create(name: str) -> ProjectOut
```

Cree un projet dont l'appelant devient proprietaire.

**Route :** `POST /api/v1/projects`, `PATCH /api/v1/projects/{project_id}`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `rename`

```python
rename(project_id: str, name: str) -> ProjectOut
```

Renomme un projet.

**Route :** `PATCH /api/v1/projects/{project_id}`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `delete`

```python
delete(project_id: str, confirmation_text: str | None, confirm: bool) -> DeletionPreviewOut | DeletionOut
```

Supprime un projet (protocole en deux temps).

**Route :** `GET /api/v1/projects/{project_id}/members`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `list_members`

```python
list_members(project_id: str, page: int, page_size: int, role: MembershipRole | str | None) -> Page[ProjectMemberOut]
```

Liste les membres d'un projet.

**Route :** `GET /api/v1/projects/{project_id}/members`, `PUT /api/v1/projects/{project_id}/members/{user_id}/rights`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `update_member_rights`

```python
update_member_rights(project_id: str, user_id: str, body: MemberRightsUpdateIn) -> ProjectMemberOut
```

Remplace le profil et/ou les droits additionnels d'un invite.

**Route :** `PUT /api/v1/projects/{project_id}/members/{user_id}/rights`, `DELETE /api/v1/projects/{project_id}/members/{user_id}`, `POST /api/v1/projects/{project_id}/invitations`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `remove_member`

```python
remove_member(project_id: str, user_id: str) -> None
```

Retire un invite du projet.

**Route :** `DELETE /api/v1/projects/{project_id}/members/{user_id}`, `POST /api/v1/projects/{project_id}/invitations`, `GET /api/v1/projects/{project_id}/invitations`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `create_invitation`

```python
create_invitation(project_id: str, body: InvitationCreateIn) -> InvitationOut
```

Invite un utilisateur dans le projet.

**Route :** `POST /api/v1/projects/{project_id}/invitations`, `GET /api/v1/projects/{project_id}/invitations`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `list_invitations`

```python
list_invitations(project_id: str, page: int, page_size: int, status: InvitationStatus | str | None, invitee_id: str | None) -> Page[InvitationOut]
```

Liste les invitations d'un projet.

**Route :** `GET /api/v1/projects/{project_id}/invitations`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.
