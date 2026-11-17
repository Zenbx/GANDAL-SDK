# Pagination

```python
from gandal_sdk import paginate

paginate(list_method, *args, page_size: int = 100, **filters) -> Iterator
```

Attend une methode qui renvoie `Page[T]` avec `items` et un total.
Ne s'applique qu'a l'orchestration (IAM = curseur).
