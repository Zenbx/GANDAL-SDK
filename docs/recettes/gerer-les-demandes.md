# Gerer les demandes

## Lister

```python
from gandal_sdk.orchestration import RequestStatus, RequestKind

page = client.orchestration.requests.list(
    status=RequestStatus.PENDING,
    kind=RequestKind.VM_CREATE,
    project_id=project_id,
)
for req in page.items:
    print(req.id, req.kind, req.author_id)
```

## Accepter / refuser (administrateur)

```python
client.orchestration.requests.accept(request_id, note="ok bac a sable")
# ou
client.orchestration.requests.refuse(request_id, note="quota projet depasse")
```

## Annuler (auteur)

```python
client.orchestration.requests.cancel(request_id)
```

## Attendre une decision

```python
accepted = client.orchestration.requests.wait_until_accepted(
    request_id, delay=15.0, max_attempts=240
)
```

`refused` et `cancelled` levent `WaiterFailure` immediatement.
