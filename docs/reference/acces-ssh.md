# AccesSsh

Certificats SSH ephemeres via le signeur, puis ouverture de session.

**Acces :** `from gandal_sdk.acces_ssh import AccesSsh`

!!! tip
    CLI : `gandal-ssh`. Jetons : `GANDAL_JETON`, signeur : `GANDAL_SIGNEUR`, CA : `GANDAL_CA`.

## `certificat`

```python
certificat(vm: str, login: str, sujet: str) -> Certificat
```

Demande un certificat pour `vm`. Lève `AccesRefuse` si c'est non.

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `commande_ssh`

```python
commande_ssh(vm: str, c: Certificat, hote: str, login: str) -> list[str]
```

La ligne `ssh` à lancer. Séparée pour pouvoir la montrer et la tester.

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `entrer`

```python
entrer(vm: str, hote: str, login: str, commande: list[str] | None) -> int
```

Obtient un certificat et ouvre la session. Rend le code de sortie.

**Exceptions :** `GandalApiError` sur erreur HTTP metier.
