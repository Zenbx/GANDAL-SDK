# Waiters

Module `gandal_sdk.waiters`.

## Constantes

- `DEFAULT_DELAY = 5.0`
- `DEFAULT_MAX_ATTEMPTS = 60`
- `GONE` - valeur renvoyee quand la ressource a disparu (404)

## `wait_for`

Moteur generique : `fetch` + `is_success` + `failure_reason` optionnel + `gone_is_success`.

Les waiters concrets vivent sur `client.orchestration.vms|storages|requests`
et `client.hypervisor`.

Guide : [Pagination et waiters](../guide/pagination-et-waiters.md).
