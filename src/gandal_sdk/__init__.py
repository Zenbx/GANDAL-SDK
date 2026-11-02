"""SDK Python GANDAL pour apps externes."""

from gandal_sdk._http import RetryPolicy
from gandal_sdk.client import GandalClient
from gandal_sdk.errors import CellUnavailable, GandalApiError, GandalError
from gandal_sdk.pagination import paginate
from gandal_sdk.waiters import WaiterError, WaiterFailure, WaiterTimeout

__all__ = [
    "GandalClient",
    "GandalError",
    "GandalApiError",
    "CellUnavailable",
    "RetryPolicy",
    "paginate",
    "WaiterError",
    "WaiterFailure",
    "WaiterTimeout",
]

__version__ = "0.4.0"
