"""Pythonic client for GRANTA MI ServerAPI JobQueue."""
import importlib.metadata as importlib_metadata

from ._connection import Connection, JobQueueApiClient
from ._models import (
    AsyncJob,
    ExcelExportJobRequest,
    ExcelImportJobRequest,
    ExportRecord,
    JobQueueProcessingConfiguration,
    JobRequest,
    JobStatus,
    JobType,
    TextImportJobRequest,
)

__all__ = [
    "AsyncJob",
    "Connection",
    "ExcelExportJobRequest",
    "ExcelImportJobRequest",
    "ExportRecord",
    "JobQueueApiClient",
    "JobQueueProcessingConfiguration",
    "JobRequest",
    "JobStatus",
    "JobType",
    "TextImportJobRequest",
]
__version__ = importlib_metadata.version(__name__.replace(".", "-"))
