# GardeIam

Sequence decider → reserver → confirmer / liberer cote client. Ce n'est **pas** le controle d'acces autoritaire (celui-ci vit dans le backend).

**Acces :** `from gandal_sdk import GardeIam`

!!! danger
    Contournable : appeler le backend directement ignore la garde.

## `decider`

```python
decider(action: str, ressource: dict[str, Any], contexte: dict[str, Any] | None = None) -> str
```

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `reserver`

```python
reserver(ressources: dict[str, int], duree_s: int, portee_ressource: str | None) -> str
```

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `confirmer`

```python
confirmer(id_ressource: str, type_ressource: str = 'vm') -> None
```

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `liberer`

```python
liberer() -> None
```

Avale l échec : la réservation expirera seule, et faire échouer le nettoyage masquerait l erreur d origine — celle que l appelant doit voir.

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `rendre`

```python
rendre(id_ressource: str) -> None
```

La ressource est détruite : son quota revient. Sans cet appel, le quota reste consommé par quelque chose qui n existe plus.

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `autoriser_creation`

```python
autoriser_creation(nom: str, vcpu: int, ram_gb: int, disk_gb: int, hote: str | None, duree_s: int) -> str
```

Décide PUIS réserve, dans cet ordre. Réserver d abord retiendrait du quota pour une demande qui va être refusée.

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `autoriser_modification`

```python
autoriser_modification(id_vm: str, vcpu: int, ram_gb: int, disk_gb: int) -> str
```

Décide, **puis** redimensionne la ressource dans IAM. ELLE COMPTE MAINTENANT. Elle ne comptait pas : le coût du catalogue IAM *ajoute*, il ne retranche pas, donc compter un redimensionnement par le

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `redimensionner`

```python
redimensionner(id_ressource: str, quantites: dict[str, int]) -> None
```

Quantités **absolues**, IAM soustrait. Les clés absentes restent inchangées : un appelant qui ne parle que de la mémoire ne doit pas effacer le compte de vCPU au passage.

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `autoriser_suppression`

```python
autoriser_suppression(id_vm: str) -> str
```

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `autoriser_alimentation`

```python
autoriser_alimentation(id_vm: str, action: str) -> str
```

`start` | `stop` | `reboot`. Un redémarrage est un arrêt suivi d un démarrage : on exige `vm:stop`, la plus forte des deux.

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `autoriser_creation_seau`

```python
autoriser_creation_seau(nom: str, fournisseur: str | None, duree_s: int) -> str
```

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `autoriser_suppression_seau`

```python
autoriser_suppression_seau(nom: str) -> str
```

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `autoriser_ecriture`

```python
autoriser_ecriture(seau: str, cle: str, octets: int, duree_s: int) -> str
```

Arrondi au Gio SUPERIEUR : facturer 0 Gio pour un fichier de 1 Mio laisserait passer un million de fichiers sans rien compter.

**Exceptions :** `GandalApiError` sur erreur HTTP metier.

## `autoriser_lecture`

```python
autoriser_lecture(seau: str, cle: str, octets: int) -> str
```

Compte la SORTIE au quota mensuel : c est l axe qui se facture, et le seul qu une boucle peut faire exploser en une nuit.

**Exceptions :** `GandalApiError` sur erreur HTTP metier.
