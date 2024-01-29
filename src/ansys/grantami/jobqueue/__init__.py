"""Pythonic client for GRANTA MI ServerAPI RecordLists."""
import importlib.metadata as importlib_metadata

from ._connection import Connection, JobQueueApiClient

__all__ = [
    "Connection",
    "JobQueueApiClient",
]
__version__ = importlib_metadata.version(__name__.replace(".", "-"))
