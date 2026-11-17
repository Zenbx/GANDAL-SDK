# Entrer dans une VM

## CLI

```bash
export GANDAL_JETON="$OIDC_ACCESS_TOKEN"
export GANDAL_SIGNEUR="https://signeur.example:8443"
# optionnel : export GANDAL_CA=~/.gandal/gandal-ca.crt
gandal-ssh poste-vision-01
```

## Python

```python
import os
from gandal_sdk.acces_ssh import AccesSsh, AccesRefuse

jeton = os.environ["GANDAL_JETON"]
try:
    with AccesSsh(jeton, signeur=os.environ["GANDAL_SIGNEUR"]) as a:
        # certificat seul
        cert = a.certificat("poste-vision-01")
        print(cert.validite, cert.expire_vers)
        # ou session interactive
        a.entrer("poste-vision-01")
except AccesRefuse as err:
    print("refuse:", err)
```

La paire de cles est creee dans un repertoire temporaire `700` et detruite a la sortie du `with`.
