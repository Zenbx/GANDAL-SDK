# App machine et STS

Pour une application serveur qui parle a IAM avec une **identite machine**.

## Creer l'identite et une cle

```python
from gandal_sdk import GandalClient
client = GandalClient.from_env()

# Corps : voir reference IAM F et openapi/gandal-iam.json
machine = client.iam.create_machine_identity(corps_machine)
# create_access_key : PAS d'Idempotency-Key (le secret ne doit pas etre rememorise)
cle = client.iam.create_access_key(...)
# stocker le secret une seule fois, hors depot git
```

## Assumer un role

```python
from gandal_sdk.cells.iam import DemandeAssomption

session = client.iam.assume_role(DemandeAssomption(...))
# utilisez le jeton de session pour les appels suivants
client.set_iam_token(session_token)
```

!!! warning
    `create_access_key` et `assume_role` ne sont **pas** rejoues automatiquement :
    un double appel creerait un second secret / une seconde session.

Voir [IAM F - Machines](../reference/iam/f-machines.md).
