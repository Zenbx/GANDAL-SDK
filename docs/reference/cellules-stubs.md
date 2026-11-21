# Cellules encore en stub

Ces cellules ne sont **pas** branchees. Chaque appel leve `CellUnavailable`.

Ne pas confondre avec l'orchestration : `client.orchestration.networks` et
`client.orchestration.storages` parlent a iaas-api. La cellule reseau est
integree (`client.network`) ; stockage / DNS / notifications restent en stub.

## Cellule stockage (stub)

**Acces :** `client.storage`

### `create_storage`

```python
create_storage(spec: StorageSpec) -> StorageRef
```

Cree un espace (pas encore disponible).

**Exceptions :** `CellUnavailable`.

### `resize`

```python
resize(ref: StorageRef, size_gb: int) -> None
```

Redimensionne un espace (pas encore disponible).

**Exceptions :** `CellUnavailable`.

### `delete_storage`

```python
delete_storage(ref: StorageRef) -> None
```

Supprime un espace (pas encore disponible).

**Exceptions :** `CellUnavailable`.

## Cellule DNS (stub)

**Acces :** `client.dns`

### `delete_domain`

```python
delete_domain(vm_id: str) -> None
```

Supprime le nom de domaine d'une VM (pas encore disponible).

**Exceptions :** `CellUnavailable`.

## Cellule notifications (stub)

**Acces :** `client.notifications`

### `notify`

```python
notify(notification: Notification) -> None
```

Envoie une notification (pas encore disponible).

**Exceptions :** `CellUnavailable`.
