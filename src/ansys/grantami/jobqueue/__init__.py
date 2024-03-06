"""Pythonic client for GRANTA MI ServerAPI JobQueue."""
import importlib.metadata as importlib_metadata

from ._connection import Connection, JobQueueApiClient
from ._models import (
    AsyncJob,
    ExcelExportJobRequest,
    ExcelImportJobRequest,
    ExportRecord,
    JobQueueProcessingConfiguration,
    JobStatus,
    JobType,
    TextImportJobRequest,
)

__all__ = [
    "Connection",
    "JobQueueApiClient",
    "ExcelImportJobRequest",
    "TextImportJobRequest",
    "JobStatus",
    "JobType",
    "AsyncJob",
    "JobQueueProcessingConfiguration",
    "ExportRecord",
    "ExcelExportJobRequest",
]
__version__ = importlib_metadata.version(__name__.replace(".", "-"))
