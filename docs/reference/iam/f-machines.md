# F - Machines, cles, STS, politiques

Identites machine, cles d'acces, assume_role, politiques.

**Acces :** `client.iam`

!!! note
    Sans endpoint IAM configure, chaque appel leve `CellUnavailable`. Les ecritures envoient une `Idempotency-Key` (sauf `create_access_key` et `assume_role`). Erreurs en `application/problem+json` → `GandalApiError`.

## `create_machine_identity`

```python
create_machine_identity(machine: m.MachineEntree | dict[str, Any], idempotency_key: str | None, correlation_id: str | None) -> dict[str, Any]
```

Cree une identite machine.

**Route :** `POST /machine-identities`, `GET /access-keys`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `list_access_keys`

```python
list_access_keys(sujet: str | None, correlation_id: str | None) -> dict[str, Any]
```

Liste les cles d'acces (sans secret).

**Route :** `GET /access-keys`, `POST /access-keys`, `DELETE /access-keys/{key_id}`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `create_access_key`

```python
create_access_key(cle: m.CleEntree | dict[str, Any] | None = None, correlation_id: str | None) -> dict[str, Any]
```

Cree une cle ; le secret n'est rendu que dans cette reponse (sans Idempotency-Key).

**Route :** `POST /access-keys`, `DELETE /access-keys/{key_id}`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `delete_access_key`

```python
delete_access_key(key_id: str, idempotency_key: str | None, correlation_id: str | None) -> dict[str, Any]
```

Supprime une cle d'acces.

**Route :** `DELETE /access-keys/{key_id}`, `PATCH /access-keys/{key_id}`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `set_access_key_status`

```python
set_access_key_status(key_id: str, statut: m.CleStatut | m.CleStatutValeur | dict[str, Any] | str, idempotency_key: str | None, correlation_id: str | None) -> dict[str, Any]
```

Active ou desactive une cle.

**Route :** `PATCH /access-keys/{key_id}`, `POST /sts/assume-role`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `assume_role`

```python
assume_role(demande: m.DemandeAssomption | dict[str, Any], correlation_id: str | None) -> dict[str, Any]
```

Endosse un role et recoit des identifiants temporaires (sans Idempotency-Key).

**Route :** `POST /sts/assume-role`, `DELETE /sts/sessions/{session_id}`, `GET /sts/whoami`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `revoke_session`

```python
revoke_session(session_id: str, idempotency_key: str | None, correlation_id: str | None) -> dict[str, Any]
```

Revoque une session STS.

**Route :** `DELETE /sts/sessions/{session_id}`, `GET /sts/whoami`, `GET /assumable-roles`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `whoami`

```python
whoami(correlation_id: str | None) -> dict[str, Any]
```

Identite effective de la session courante (STS).

**Route :** `GET /sts/whoami`, `GET /assumable-roles`, `POST /assumable-roles`, `GET /assumable-roles/{name}`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `list_assumable_roles`

```python
list_assumable_roles(correlation_id: str | None) -> dict[str, Any]
```

Roles assumables.

**Route :** `GET /assumable-roles`, `POST /assumable-roles`, `GET /assumable-roles/{name}`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `create_assumable_role`

```python
create_assumable_role(role: m.RoleEntree | dict[str, Any], idempotency_key: str | None, correlation_id: str | None) -> dict[str, Any]
```

Cree un role assumable.

**Route :** `POST /assumable-roles`, `GET /assumable-roles/{name}`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `get_assumable_role`

```python
get_assumable_role(name: str, correlation_id: str | None) -> dict[str, Any]
```

Lit un role assumable.

**Route :** `GET /assumable-roles/{name}`, `DELETE /assumable-roles/{name}`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `delete_assumable_role`

```python
delete_assumable_role(name: str, idempotency_key: str | None, correlation_id: str | None) -> dict[str, Any]
```

Supprime un role assumable.

**Route :** `DELETE /assumable-roles/{name}`, `PUT /assumable-roles/{role_name}/policies/{policy_name}`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `attach_policy_to_role`

```python
attach_policy_to_role(role_name: str, policy_name: str, idempotency_key: str | None, correlation_id: str | None) -> dict[str, Any]
```

Attache une politique a un role assumable.

**Route :** `PUT /assumable-roles/{role_name}/policies/{policy_name}`, `DELETE /assumable-roles/{role_name}/policies/{policy_name}`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `detach_policy_from_role`

```python
detach_policy_from_role(role_name: str, policy_name: str, idempotency_key: str | None, correlation_id: str | None) -> dict[str, Any]
```

Detache une politique d'un role assumable.

**Route :** `DELETE /assumable-roles/{role_name}/policies/{policy_name}`, `POST /assumable-roles/{role_name}/revoke-sessions`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `revoke_role_sessions`

```python
revoke_role_sessions(role_name: str, idempotency_key: str | None, correlation_id: str | None) -> dict[str, Any]
```

Revoque toutes les sessions d'un role.

**Route :** `POST /assumable-roles/{role_name}/revoke-sessions`, `GET /policies`, `POST /policies`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `list_policies`

```python
list_policies(correlation_id: str | None) -> dict[str, Any]
```

Liste les politiques.

**Route :** `GET /policies`, `POST /policies`, `GET /policies/{name}`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `create_policy`

```python
create_policy(politique: m.PolitiqueEntree | dict[str, Any], idempotency_key: str | None, correlation_id: str | None) -> dict[str, Any]
```

Cree une politique.

**Route :** `POST /policies`, `GET /policies/{name}`, `DELETE /policies/{name}`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `get_policy`

```python
get_policy(name: str, correlation_id: str | None) -> dict[str, Any]
```

Lit une politique.

**Route :** `GET /policies/{name}`, `DELETE /policies/{name}`, `POST /policies/{name}/attachments`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `delete_policy`

```python
delete_policy(name: str, idempotency_key: str | None, correlation_id: str | None) -> dict[str, Any]
```

Supprime une politique.

**Route :** `DELETE /policies/{name}`, `POST /policies/{name}/attachments`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `attach_policy`

```python
attach_policy(name: str, attachement: m.AttachementEntree | dict[str, Any], idempotency_key: str | None, correlation_id: str | None) -> dict[str, Any]
```

Attache une politique a une cible.

**Route :** `POST /policies/{name}/attachments`, `DELETE /policies/{name}/attachments/organisation`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `detach_policy_organisation`

```python
detach_policy_organisation(name: str, idempotency_key: str | None, correlation_id: str | None) -> dict[str, Any]
```

Detache une politique de l'organisation.

**Route :** `DELETE /policies/{name}/attachments/organisation`, `DELETE /policies/{name}/attachments/{cible_type}/{cible}`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `detach_policy`

```python
detach_policy(name: str, cible_type: str, cible: str, idempotency_key: str | None, correlation_id: str | None) -> dict[str, Any]
```

Detache une politique d'une cible.

**Route :** `DELETE /policies/{name}/attachments/{cible_type}/{cible}`, `POST /policies:generate`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `generate_base_policies`

```python
generate_base_policies(demande: m.DemandeEngendrer | dict[str, Any] | None = None, idempotency_key: str | None, correlation_id: str | None) -> dict[str, Any]
```

Engendre les politiques de base.

**Route :** `POST /policies:generate`, `POST /policies:simulate`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `simulate_policies`

```python
simulate_policies(demande: m.DemandeSimulation | dict[str, Any], correlation_id: str | None) -> dict[str, Any]
```

Simule l'evaluation de politiques sans effet de bord.

**Route :** `POST /policies:simulate`, `GET /policy-context-keys`, `GET /resources/{resource_id}`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `list_policy_context_keys`

```python
list_policy_context_keys(correlation_id: str | None) -> dict[str, Any]
```

Cles de contexte utilisables dans les politiques.

**Route :** `GET /policy-context-keys`, `GET /resources/{resource_id}`, `POST /resources/{resource_id}/grants`

**Exceptions :** `GandalApiError` sur erreur HTTP metier.
