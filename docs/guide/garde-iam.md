# Garde IAM

`GardeIam` enchaine **decider → reserver → confirmer** (ou liberer en cas d'echec).

!!! danger
    Ce n'est **pas** le controle d'acces autoritaire. Un client qui appelle le backend
    directement contourne la garde. L'autorite vit cote serveur.

## Prefrequis

- `GANDAL_IAM_ENDPOINT` (+ jeton) configure
- Un `sujet` explicite (obligatoire)

## Exemple creation VM

```python
from gandal_sdk import GandalClient, GardeIam, DecisionRefusee
from gandal_sdk.orchestration import VMCreateRequestIn

client = GandalClient.from_env()

try:
    with GardeIam(client.iam, sujet="etu-1", projet="prj_vision") as g:
        g.autoriser_creation("poste-1", vcpu=2, ram_gb=4, disk_gb=20)
        demande = client.orchestration.vms.request_create(
            "prj_vision",
            VMCreateRequestIn(name="poste-1", pack_id="pack-standard"),
        )
        # apres acceptation admin et creation reelle :
        # g.confirmer(vm_id, "vm")
except DecisionRefusee as err:
    print(err.motif, err.explication)
```

Si le corps du `with` leve, `__exit__` appelle `liberer()` : la reservation n'enferme pas le quota.

## Modification (`vm:update`)

`autoriser_modification` decide puis appelle `resize_resource` avec des quantites **absolues**
(c'est IAM qui calcule l'ecart).

Voir [reference GardeIam](../reference/garde.md).
