"""SDK Python GANDAL pour apps externes."""

from gandal_sdk.client import GandalClient
from gandal_sdk.errors import CellUnavailable, GandalApiError, GandalError

__all__ = [
    "GandalClient",
    "GandalError",
    "GandalApiError",
    "CellUnavailable",
]

__version__ = "0.1.0"
