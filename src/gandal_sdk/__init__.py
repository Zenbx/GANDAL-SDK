"""SDK Python GANDAL pour apps externes."""

from gandal_sdk._http import RetryPolicy
from gandal_sdk.client import GandalClient
from gandal_sdk.errors import CellUnavailable, GandalApiError, GandalError
from gandal_sdk.pagination import paginate

__all__ = [
    "GandalClient",
    "GandalError",
    "GandalApiError",
    "CellUnavailable",
    "RetryPolicy",
    "paginate",
]

__version__ = "0.2.0"
