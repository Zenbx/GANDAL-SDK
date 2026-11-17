# Creer une VM

Parcours metier via l'orchestration (demande admin).

## Sans garde IAM

```python
from gandal_sdk import GandalClient
from gandal_sdk.orchestration import VMCreateRequestIn, PowerAction

client = GandalClient.from_env()
client.login("alice@iaas.cm", "alice123")  # si pas de token dans from_env

project_id = client.orchestration.projects.list().items[0].id

req = client.orchestration.vms.request_create(
    project_id,
    VMCreateRequestIn(name="web-01", pack_id="pack-standard"),
)

# cote admin (autre session) :
# client.orchestration.requests.accept(req.id)

accepted = client.orchestration.requests.wait_until_accepted(req.id)
vm_id = accepted.target_resource_id
vm = client.orchestration.vms.wait_until_running(project_id, vm_id)
print(vm.name, vm.ip_address)

client.orchestration.vms.power(project_id, vm_id, PowerAction.START)
```

## Avec GardeIam

```python
from gandal_sdk import GandalClient, GardeIam
from gandal_sdk.orchestration import VMCreateRequestIn

client = GandalClient.from_env()
project_id = "prj_vision"

with GardeIam(client.iam, sujet="etu-1", projet=project_id) as g:
    g.autoriser_creation("web-01", vcpu=2, ram_gb=4, disk_gb=20)
    req = client.orchestration.vms.request_create(
        project_id,
        VMCreateRequestIn(name="web-01", pack_id="pack-standard"),
    )
    accepted = client.orchestration.requests.wait_until_accepted(req.id)
    g.confirmer(accepted.target_resource_id, "vm")
```

## Suite

- [Gerer les demandes](gerer-les-demandes.md)
- [Entrer dans une VM](entrer-dans-une-vm.md)
