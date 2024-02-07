"""Pythonic client for GRANTA MI ServerAPI RecordLists."""
import importlib.metadata as importlib_metadata

from ._connection import Connection, JobQueueApiClient
from ._models import ExcelImportJobRequest, JobStatus, TextImportJobRequest

__all__ = [
    "Connection",
    "JobQueueApiClient",
    "ExcelImportJobRequest",
    "TextImportJobRequest",
    "JobStatus",
]
__version__ = importlib_metadata.version(__name__.replace(".", "-"))
