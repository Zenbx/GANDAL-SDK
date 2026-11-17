# Hyperviseur

`client.hypervisor` pilote les VM du **pool** via gandal-hypervisor.

## Quand l'utiliser

- Ops plateforme / scripts d'infra sur le pool
- **Pas** le chemin metier etudiant : preferer `client.orchestration.vms` (demandes)

## Exemple

```python
from gandal_sdk import GandalClient
from gandal_sdk.cells.hypervisor import PowerAction, VmSpec

client = GandalClient.from_env()  # GANDAL_HYPERVISOR_ENDPOINT requis

created = client.hypervisor.create_vm(
    VmSpec(name="sdk-it-web", ram_gb=1, vcpu=1, vram_gb=0, ssd_gb=10)
)
client.hypervisor.wait_for_operation(created.operation)
vm = client.hypervisor.wait_until_running(created.vm)
print(vm.ip_address)

client.hypervisor.power(vm, PowerAction.STOP)
client.hypervisor.wait_until_stopped(vm)
client.hypervisor.delete_vm(vm)
client.hypervisor.wait_until_deleted(vm)
```

Sans endpoint : `CellUnavailable`.

Voir [reference hyperviseur](../reference/hyperviseur.md).
