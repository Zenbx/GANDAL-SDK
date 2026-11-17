# D - Projets et acces

Projets IAM, membres, demandes d'acces.

**Acces :** `client.iam`

!!! note
    Sans endpoint IAM configure, chaque appel leve `CellUnavailable`. Les ecritures envoient une `Idempotency-Key` (sauf `create_access_key` et `assume_role`). Erreurs en `application/problem+json` → `GandalApiError`.

## `list_projects`

```python
list_projects(curseur: str | None, taille: int | None, correlation_id: str | None) -> m.PageProjets
```

Liste paginee des projets visibles.

**Route :** `GET /projects`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `create_project`

```python
create_project(nom: str, description: str | None, environnement: m.Environnement | str | None, plan: str | None, idempotency_key: str | None, correlation_id: str | None) -> m.Projet
```

Cree un projet.

**Route :** `POST /projects`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `get_project`

```python
get_project(project_id: str, correlation_id: str | None) -> m.Projet
```

Lit un projet.

**Route :** `GET /projects/{project_id}`, `DELETE /projects/{project_id}`, `GET /projects/{project_id}/members`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `archive_project`

```python
archive_project(project_id: str, idempotency_key: str | None, correlation_id: str | None) -> m.Projet
```

Archive un projet.

**Route :** `DELETE /projects/{project_id}`, `GET /projects/{project_id}/members`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `list_members`

```python
list_members(project_id: str, correlation_id: str | None) -> m.MembresProjet
```

Membres d'un projet.

**Route :** `GET /projects/{project_id}/members`, `POST /projects/{project_id}/members`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `invite_member`

```python
invite_member(project_id: str, sujet: str, capacite: m.Capacite | str, fin_a: str | None, motif: str | None, idempotency_key: str | None, correlation_id: str | None) -> m.Membre
```

Invite un sujet existant dans un projet.

**Route :** `POST /projects/{project_id}/members`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `remove_member`

```python
remove_member(project_id: str, subject_id: str, idempotency_key: str | None, correlation_id: str | None) -> None
```

Retire un membre d'un projet.

**Route :** `DELETE /projects/{project_id}/members/{subject_id}`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `change_member_capacity`

```python
change_member_capacity(project_id: str, subject_id: str, capacite: m.Capacite | str, fin_a: str | None, motif: str | None, idempotency_key: str | None, correlation_id: str | None) -> m.Membre
```

Change la capacite d'un membre.

**Route :** `PATCH /projects/{project_id}/members/{subject_id}`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `create_member`

```python
create_member(project_id: str, membre: m.MembreNouveau | dict[str, Any], idempotency_key: str | None, correlation_id: str | None) -> dict[str, Any]
```

Cree un compte et l'ajoute au projet en un appel.

**Route :** `POST /projects/{project_id}/members:create`, `POST /projects/{project_id}/transfer`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `transfer_project`

```python
transfer_project(project_id: str, nouveau_proprietaire: str, motif: str | None, idempotency_key: str | None, correlation_id: str | None) -> m.Projet
```

Transfere la propriete d'un projet.

**Route :** `POST /projects/{project_id}/transfer`, `GET /access-requests`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `list_access_requests`

```python
list_access_requests(correlation_id: str | None) -> m.PageDemandesAcces
```

Liste les demandes d'acces.

**Route :** `GET /access-requests`, `POST /access-requests`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `request_access`

```python
request_access(projet: str, capacite: m.Capacite | str, motif: str | None, fin_a: str | None, duree_s: int | None, idempotency_key: str | None, correlation_id: str | None) -> m.DemandeAcces
```

Demande l'acces a un projet.

**Route :** `POST /access-requests`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `decide_access_request`

```python
decide_access_request(request_id: str, verdict: str, capacite: m.Capacite | str | None, fin_a: str | None, motif: str | None, idempotency_key: str | None, correlation_id: str | None) -> m.DemandeAcces
```

Approuve ou refuse une demande d'acces.

**Route :** `POST /access-requests/{request_id}/decide`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.
