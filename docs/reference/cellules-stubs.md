# Cellules encore en stub

Ces cellules ne sont **pas** branchees. Chaque appel leve `CellUnavailable`.

Ne pas confondre avec l'orchestration : `client.orchestration.networks` et `client.orchestration.storages` parlent a iaas-api ; `client.network` / `client.storage` parleront aux futures cellules.

# Cellule DNS (stub)

Stub : chaque methode leve `CellUnavailable` tant que l'API cellule n'est pas livree. Pour le reseau / stockage metier aujourd'hui, utiliser `client.orchestration.networks` / `storages`.

**Acces :** `client.dns`

## `delete_domain`

```python
delete_domain(vm_id: str) -> None
```

Supprime le nom de domaine d'une VM (pas encore disponible).

**Exceptions :** `GandalApiError` sur erreur HTTP metier.


# Cellule reseau (stub)

Stub : chaque methode leve `CellUnavailable` tant que l'API cellule n'est pas livree. Pour le reseau / stockage metier aujourd'hui, utiliser `client.orchestration.networks` / `storages`.

**Acces :** `client.network`

## `create_network`

```python
create_network(project_id: str, name: str) -> NetworkRef
```

Cree un reseau (pas encore disponible).

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `rename_network`

```python
rename_network(network: NetworkRef, name: str) -> None
```

Renomme un reseau (pas encore disponible).

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `attach_vm`

```python
attach_vm(network: NetworkRef, vm: VmRef) -> None
```

Rattache une VM a un reseau (pas encore disponible).

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `detach_vm`

```python
detach_vm(network: NetworkRef, vm: VmRef) -> None
```

Detache une VM d'un reseau (pas encore disponible).

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `detach_vm_from_project`

```python
detach_vm_from_project(vm: VmRef, project_id: str) -> None
```

Retire une VM de tous les reseaux d'un projet (pas encore disponible).

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `delete_network`

```python
delete_network(network: NetworkRef) -> None
```

Supprime un reseau (pas encore disponible).

**Exceptions :** `GandalApiError` sur erreur HTTP metier.


# Cellule notifications (stub)

Stub : chaque methode leve `CellUnavailable` tant que l'API cellule n'est pas livree. Pour le reseau / stockage metier aujourd'hui, utiliser `client.orchestration.networks` / `storages`.

**Acces :** `client.notifications`

## `notify`

```python
notify(notification: Notification) -> None
```

Envoie une notification (pas encore disponible).

**Exceptions :** `GandalApiError` sur erreur HTTP metier.


# Cellule stockage (stub)

Stub : chaque methode leve `CellUnavailable` tant que l'API cellule n'est pas livree. Pour le reseau / stockage metier aujourd'hui, utiliser `client.orchestration.networks` / `storages`.

**Acces :** `client.storage`

## `create_storage`

```python
create_storage(spec: StorageSpec) -> StorageRef
```

Cree un espace (pas encore disponible).

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `resize`

```python
resize(ref: StorageRef, size_gb: int) -> None
```

Redimensionne un espace (pas encore disponible).

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `delete_storage`

```python
delete_storage(ref: StorageRef) -> None
```

Supprime un espace (pas encore disponible).

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

