# Requests

Moteur de demandes (creation / modification de ressources).

**Acces :** `client.orchestration.requests`

!!! warning
    `RequestOut.id` est une **chaine** (UUID), pas un entier.

## `list`

```python
list(page: int, page_size: int, status: RequestStatus | str | None, kind: RequestKind | str | None, project_id: str | None, author_id: str | None) -> Page[RequestOut]
```

Liste les demandes visibles.

**Route :** `GET /api/v1/requests`, `GET /api/v1/requests/{request_id}`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `get`

```python
get(request_id: str) -> RequestOut
```

Consulte une demande.

**Route :** `GET /api/v1/requests/{request_id}`, `POST /api/v1/requests/{request_id}/cancel`, `POST /api/v1/requests/{request_id}/accept`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `cancel`

```python
cancel(request_id: str) -> RequestOut
```

Annule une demande en attente (auteur).

**Route :** `POST /api/v1/requests/{request_id}/cancel`, `POST /api/v1/requests/{request_id}/accept`, `POST /api/v1/requests/{request_id}/refuse`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `accept`

```python
accept(request_id: str, note: str | None) -> RequestOut
```

Accepte une demande (administrateur).

**Route :** `POST /api/v1/requests/{request_id}/accept`, `POST /api/v1/requests/{request_id}/refuse`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `refuse`

```python
refuse(request_id: str, note: str | None) -> RequestOut
```

Refuse une demande (administrateur).

**Route :** `POST /api/v1/requests/{request_id}/refuse`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `wait_until_accepted`

```python
wait_until_accepted(request_id: str, delay: float, max_attempts: int) -> RequestOut
```

Attend l'acceptation d'une demande par un administrateur. Leve WaiterFailure si elle est refusee ou annulee. Pour une creation, target_resource_id de la demande renvoyee designe la ressource creee.

**Exceptions :** `GandalApiError` sur erreur HTTP metier.
