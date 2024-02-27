from abc import ABC, abstractmethod
from dataclasses import dataclass
import datetime
from enum import Enum
from io import BufferedIOBase, RawIOBase
import json
import os
import pathlib
from typing import Any, BinaryIO, Dict, List, Optional, Union
import warnings

from ansys.grantami.serverapi_openapi import api, models
from ansys.openapi.common import UndefinedObjectWarning, Unset

File_Type = Union[str, pathlib.Path, BinaryIO]


class JobStatus(Enum):
    """Provides possible states of a job in the job queue."""

    Pending = models.GrantaServerApiAsyncJobsJobStatus.PENDING.value, """Job is in the queue"""
    Running = (
        models.GrantaServerApiAsyncJobsJobStatus.RUNNING.value,
        """Job is currently executing""",
    )
    Succeeded = (
        models.GrantaServerApiAsyncJobsJobStatus.SUCCEEDED.value,
        """Job has completed (does not guarantee that no errors occurred)""",
    )
    Failed = models.GrantaServerApiAsyncJobsJobStatus.FAILED.value, """Job could not complete"""
    Cancelled = (
        models.GrantaServerApiAsyncJobsJobStatus.CANCELLED.value,
        """Job was cancelled by the user""",
    )
    Deleted = "Deleted", """Job was deleted on the server"""


class JobType(Enum):
    """Provides possible job types."""

    ExcelImportJob = "ExcelImportJob"
    ExcelExportJob = "ExcelExportJob"
    TextImportJob = "TextImportJob"


class ImportJobRequest(ABC):
    """
    Abstract base class representing an import job request.

    Each subclass represents a specific import type and may override some steps of the import
    process. They also add additional file types and properties as required.

    Parameters
    ----------
    name
        The name of the job as displayed in the job queue.
    description
        The description of the job as displayed in the job queue.
    scheduled_execution_date
        The earliest date and time the job should be executed.
    """

    @abstractmethod
    def __init__(
        self,
        name: str,
        description: str,
        scheduled_execution_date: Optional[datetime.datetime] = None,
    ) -> None:
        self.name = name
        self.description = description
        self.scheduled_execution_date = scheduled_execution_date
        # e.g. Dict["Template", Dict["My_template.xlsx", Dict["filePath", "C:\my_template.xlsx"]]]
        self.files: Dict[str, Dict[str, Dict[str, File_Type]]] = {}
        self.__file_ids: List[str] = []

    @abstractmethod
    def __repr__(self) -> str:
        """Printable representation of the object."""
        pass

    def _process_files(self, file_struct: Dict[str, Optional[List[File_Type]]]) -> None:
        for file_type, file_list in file_struct.items():
            if file_list is not None:
                for file in file_list:
                    self._add_file(file, file_type)

    def _add_file(self, file_obj: File_Type, type_: str) -> None:
        if type_ not in self.files:
            self.files[type_] = {}
        if isinstance(file_obj, (pathlib.Path, BufferedIOBase, RawIOBase)):
            if file_obj.name not in self.files[type_]:
                self.files[type_][file_obj.name] = {}
                self.files[type_][file_obj.name]["filePath"] = file_obj
        elif isinstance(file_obj, str):
            self.files[type_][file_obj] = {}
            self.files[type_][file_obj]["filePath"] = file_obj
        else:
            raise TypeError(
                "file_obj must be a pathlib.Path, BinaryIO, or str object. "
                f"Object provided was of type {type(file_obj)}."
            )

    def _post_files(self, api_client: api.JobQueueApi) -> None:
        for file_type, file_list in self.files.items():
            for file_name, file_obj in file_list.items():
                file_content = file_obj["filePath"]
                file_id = api_client.v1alpha_job_queue_files_post(
                    file=file_obj["filePath"],  # type: ignore[arg-type]
                )
                file_obj["id"] = file_id
                try:
                    file_obj["name"] = os.path.basename(file_name)
                except TypeError:
                    file_obj["name"] = file_name.name  # type: ignore[attr-defined]
                self.__file_ids.append(file_id)

    def _generate_file_list_for_import(self) -> List[Dict[str, File_Type]]:
        file_params = []
        for file_type, files in self.files.items():
            for file_obj in files.values():
                file_params.append({"fileType": file_type, "filePath": file_obj["name"]})
        return file_params

    def _render_file_parameters(self) -> str:
        file_params = self._generate_file_list_for_import()
        return json.dumps(file_params)

    def get_job_for_import(self) -> models.GrantaServerApiAsyncJobsCreateJobRequest:
        """
        Create an AsyncJobs ``JobRequest`` object ready for import.

        Should be called after uploading files to the service.

        Returns
        -------
        JobRequest
            The JobRequest object to be submitted to the server.
        """
        job_parameters = self._render_file_parameters()
        job_request = models.GrantaServerApiAsyncJobsCreateJobRequest(
            type=self._import_type.value,
            name=self.name,
            description=self.description,
            scheduled_execution_date=self.scheduled_execution_date,
            input_file_ids=self.__file_ids,
            parameters=job_parameters,
        )
        return job_request

    @abstractmethod
    def check_valid_for_import(self) -> None:
        """
        Verify that the import job can run.

        Raises
        ------
        ValueError
            If not enough files have been provided for the import to successfully complete.

        """
        pass

    @property
    @abstractmethod
    def _import_type(self) -> JobType:
        pass


class ExcelImportJobRequest(ImportJobRequest):
    """
    Represents an Excel import job request.

    Supports either combined imports (with template and data in the same file), or separate data
    and template imports.

    Parameters
    ----------
    name
        The name of the job as displayed in the job queue.
    description
        The description of the job as displayed in the job queue.
    scheduled_execution_date
        The earliest date and time the job should be executed.
    data_files
        Excel files containing data to be imported.
    template_files
        Excel template files.
    combined_files
        Excel files containing data and template information.
    attachment_files
        Any other files referenced in the data or combined files.
    """

    def __init__(
        self,
        name: str,
        description: str,
        scheduled_execution_date: Optional[datetime.datetime] = None,
        data_files: Optional[List[File_Type]] = None,
        template_files: Optional[List[File_Type]] = None,
        combined_files: Optional[List[File_Type]] = None,
        attachment_files: Optional[List[File_Type]] = None,
    ):
        super().__init__(name, description, scheduled_execution_date)
        self._process_files(
            {
                "Data": data_files,
                "Template": template_files,
                "Combined": combined_files,
                "Attachment": attachment_files,
            }
        )
        self.check_valid_for_import()

    def __repr__(self) -> str:
        """Printable representation of the object."""
        return f"<ExcelImportJobRequest '{self.name}'>"

    def check_valid_for_import(self) -> None:
        """
        Verify that the import job can run.

        Raises
        ------
        ValueError
            If not enough files have been provided for the import to successfully complete.

        """
        if "Combined" in self.files:
            if "Data" in self.files or "Template" in self.files:
                raise ValueError(
                    "Cannot create Excel import job with both combined and template/data files specified"
                )
        elif not ("Data" in self.files and "Template" in self.files):
            raise ValueError(
                "Excel import jobs must contain either a 'Combined' file or 'Data' files and a 'Template' file."
            )

    @property
    def _import_type(self) -> JobType:
        return JobType.ExcelImportJob


class TextImportJobRequest(ImportJobRequest):
    """
    Represents a Text import job request. Requires a template file and one or more data files.

    Parameters
    ----------
    name
        The name of the job as displayed in the job queue.
    description
        The description of the job as displayed in the job queue.
    scheduled_execution_date
        The earliest date and time the job should be executed.
    data_files
        Text files containing data to be imported.
    template_files
        Text importer template file.
    attachment_files
        Any other files referenced in the data files.
    """

    def __init__(
        self,
        name: str,
        description: str,
        scheduled_execution_date: Optional[datetime.datetime] = None,
        data_files: Optional[List[File_Type]] = None,
        template_files: Optional[List[File_Type]] = None,
        attachment_files: Optional[List[File_Type]] = None,
    ):
        super().__init__(name, description, scheduled_execution_date)
        self._process_files(
            {
                "Data": data_files,
                "Template": template_files,
                "Attachment": attachment_files,
            }
        )
        self.check_valid_for_import()

    def __repr__(self) -> str:
        """Printable representation of the object."""
        return f"<TextImportJobRequest '{self.name}'>"

    def check_valid_for_import(self) -> None:
        """
        Verify that the import job can run.

        Raises
        ------
        ValueError
            If not enough files have been provided for the import to successfully complete.

        """
        if not ("Data" in self.files and "Template" in self.files):
            raise ValueError("Text import jobs must contain 'Data' files and a 'Template' file")

    @property
    def _import_type(self) -> JobType:
        return JobType.TextImportJob


class AsyncJob:
    """
    Represents a Job on the server.

    Provides information on the current status of the Job, as well as any job specific outputs.
    Allows modification of Job metadata, such as Name, Description and Scheduled Date.

    .. note::
        Do not instantiate this class directly. Objects of this type will be returned from
        :meth:`~JobQueueApiClient.create_import_job` and
        :meth:`~JobQueueApiClient.create_import_job_and_wait` methods.
    """

    def __init__(
        self, job_obj: models.GrantaServerApiAsyncJobsJob, job_queue_api: api.JobQueueApi
    ) -> None:
        self._job_queue_api = job_queue_api
        self._is_deleted = False

        self._id: str
        self._name: str
        self._description: str
        self._status: models.GrantaServerApiAsyncJobsJobStatus
        self._type: str
        self._position: Optional[int]
        self._submitter_name: str
        self._submission_date: datetime.datetime
        self._submitter_roles: List[str]
        self._completion_datetime: Optional[datetime.datetime]
        self._execution_datetime: Optional[datetime.datetime]
        self._scheduled_exec_datetime: Optional[datetime.datetime]
        self._job_specific_outputs: Optional[Dict[str, Any]]
        self._output_files: Optional[List[str]]

        self._update_job(job_obj)

    def _update_job(self, job_obj: models.GrantaServerApiAsyncJobsJob) -> None:
        self._id = self._get_property(job_obj, name="id", required=True)
        self._name = self._get_property(job_obj, name="name", required=True)
        self._description = self._get_property(job_obj, name="description", required=True)
        self._status = self._get_property(job_obj, name="status", required=True)
        self._type = self._get_property(job_obj, name="type", required=True)
        self._position = self._get_property(job_obj, name="position")
        self._submitter_name = self._get_property(job_obj, name="submitter_name", required=True)
        self._submission_date = self._get_property(job_obj, name="submission_date", required=True)
        self._submitter_roles = self._get_property(job_obj, name="submitter_roles", required=True)
        self._completion_datetime = self._get_property(job_obj, name="completion_date")
        self._execution_datetime = self._get_property(job_obj, name="execution_date")
        self._scheduled_exec_datetime = self._get_property(job_obj, name="scheduled_execution_date")
        self._job_specific_outputs = self._get_property(job_obj, name="job_specific_outputs")
        self._output_files = self._get_property(job_obj, name="output_file_names")

    @staticmethod
    def _get_property(
        job_obj: models.GrantaServerApiAsyncJobsJob, name: str, required: bool = False
    ) -> Any:
        value = job_obj.__getattribute__(name)
        if not required:
            return value if value not in [None, Unset] else None
        elif not value:
            raise ValueError(f'Job with id: "{job_obj.id}" has no required field "{name}"')
        return value

    def __repr__(self) -> str:
        """Printable representation of the object."""
        return f"<AsyncJob '{self.name}' status '{self.status}'>"

    @property
    def id(self) -> str:
        """
        Unique job identifier in GUID form. Recommended way to refer to individual jobs.

        Returns
        -------
        str
        """
        return self._id

    @property
    def name(self) -> str:
        """
        Display name of the job (not unique).

        Returns
        -------
        str
        """
        return self._name

    def update_name(self, value: str) -> None:
        """
        Update the display name of the job on the server.

        Parameters
        ----------
        value
            The new name for this job.

        Raises
        ------
        ValueError
            If the job has been deleted from the server.
        """
        if self._is_deleted:
            raise ValueError("Job has been deleted from the Job Queue")
        patch_req = models.GrantaServerApiAsyncJobsUpdateJobRequest(
            name=value,
        )
        patch_resp = self._job_queue_api.v1alpha_job_queue_jobs_id_patch(id=self.id, body=patch_req)
        assert patch_resp
        self._name = self._get_property(patch_resp, name="name", required=True)

    @property
    def description(self) -> Optional[str]:
        """
        Description of the job as displayed in Granta MI.

        Returns
        -------
        str
        """
        return self._description

    def update_description(self, value: str) -> None:
        """
        Update the job description on the server.

        Parameters
        ----------
        value
            The new description for this job.

        Raises
        ------
        ValueError
            If the job has been deleted from the server.
        """
        if self._is_deleted:
            raise ValueError("Job has been deleted from the Job Queue")
        patch_req = models.GrantaServerApiAsyncJobsUpdateJobRequest(
            description=value,
        )
        patch_resp = self._job_queue_api.v1alpha_job_queue_jobs_id_patch(id=self.id, body=patch_req)
        assert patch_resp
        self._description = self._get_property(patch_resp, name="description")

    @property
    def status(self) -> JobStatus:
        """
        Job status of this job on the server.

        Returns
        -------
        JobStatus
        """
        if self._is_deleted:
            return JobStatus["Deleted"]
        return JobStatus[self._status.value]

    @property
    def type(self) -> JobType:
        """
        The type of this job on the server.

        Returns
        -------
        JobType
        """
        return JobType[self._type]

    @property
    def position(self) -> Union[int, None]:
        """
        Position of this job in the Job Queue.

        Returns
        -------
        int | None
            Returns ``None`` if the job is not currently pending.
        """
        return self._position

    def move_to_top(self) -> None:
        """Promotes the job to the top of the Job Queue. User must have MI_ADMIN permission."""
        self._job_queue_api.v1alpha_job_queue_jobs_idmove_to_top_post(id=self.id)
        self.update()

    @property
    def submitter_information(
        self,
    ) -> Dict[str, Union[str, datetime.datetime, List[str]]]:
        """
        Information about the job submission.

        Returns
        -------
        Dict
            The ``username`` of the submitter, ``date_time`` of submission, and the ``roles``
            to which the submitter belongs indexed by name.
        """
        return {
            "username": self._submitter_name,
            "date_time": self._submission_date,
            "roles": self._submitter_roles,
        }

    @property
    def completion_date_time(self) -> Optional[datetime.datetime]:
        """
        Date and time of job completion.

        Returns
        -------
        datetime.datetime | None
            Returns ``None`` if job is pending.
        """
        return self._completion_datetime

    @property
    def execution_date_time(self) -> Optional[datetime.datetime]:
        """
        Date and time of job execution.

        Returns
        -------
        datetime.datetime | None
            Returns ``None`` if job is pending.
        """
        return self._execution_datetime

    @property
    def scheduled_execution_date_time(self) -> Optional[datetime.datetime]:
        """
        Date and time of scheduled job execution.

        Returns
        -------
        datetime.datetime | None
            Returns ``None`` if job is not scheduled.
        """
        return self._scheduled_exec_datetime

    def update_scheduled_execution_date_time(self, value: datetime.datetime) -> None:
        """
        Update the scheduled execution time on the server.

        Parameters
        ----------
        value
            The new scheduled execution time.

        Raises
        ------
        ValueError
            If the job has been deleted from the server.
        """
        if self._is_deleted:
            raise ValueError("Job has been deleted from the Job Queue")
        patch_req = models.GrantaServerApiAsyncJobsUpdateJobRequest(
            scheduled_execution_date=value,
        )
        patch_resp = self._job_queue_api.v1alpha_job_queue_jobs_id_patch(id=self.id, body=patch_req)
        assert patch_resp
        self._scheduled_exec_datetime = (
            patch_resp.scheduled_execution_date if patch_resp.scheduled_execution_date else None
        )

    @property
    def output_information(self) -> Dict[str, Any]:
        """
        Provide additional information if supported by the job type.

        Additional information includes record placement or verbose logging. The addition is
        dependent on the details of the job.

        Returns
        -------
        Dict
            Any job-specific outputs.
        """
        parsed = {}
        for k, v in self._job_specific_outputs.items():  # type: ignore[union-attr]
            assert isinstance(v, str)
            parsed[k] = json.loads(v)
        return parsed

    @property
    def output_file_names(self) -> Union[List[str], None]:
        """
        List of file names produced by the job, for example log files.

        Returns
        -------
        List[str]
            List of file names.
        """
        return self._output_files

    def download_file(self, remote_file_name: str, file_path: Union[str, pathlib.Path]) -> None:
        """
        Download an output file from the server by name and save it to a specified location.

        Parameters
        ----------
        remote_file_name
            File name provided by :meth:`output_file_names`
        file_path
            Path where the file should be saved.

        Raises
        ------
        KeyError
            If the file name does not exist for this job.
        ValueError
            If the job has been deleted from the server.
        """
        if self._is_deleted:
            raise ValueError("Job has been deleted from the Job Queue")
        if self.output_file_names is None:
            raise ValueError("Job has no output files")
        if remote_file_name not in self.output_file_names:
            raise KeyError(f"File with name {remote_file_name} does not exist for this job")
        downloaded_file_path = self._job_queue_api.v1alpha_job_queue_jobs_id_outputsexport_get(
            id=self.id, file_name=remote_file_name
        )
        if not downloaded_file_path:
            return
        if isinstance(file_path, str):
            file_path = pathlib.Path(file_path)
        if file_path.is_dir():
            remote_name = pathlib.Path(remote_file_name).name
            file_path = file_path / remote_name
        os.rename(downloaded_file_path, file_path)

    def get_file_content(self, remote_file_name: str) -> bytes:
        """
        Download an output file from the server by name and return the file contents.

        Parameters
        ----------
        remote_file_name
            File name provided by :meth:`output_file_names`.

        Returns
        -------
        bytes
            The content of the specified file.

        Raises
        ------
        KeyError
            If the file name does not exist for this job.
        ValueError
            If the job has been deleted from the server.
        """
        if self._is_deleted:
            raise ValueError("Job has been deleted from the Job Queue")
        if self.output_file_names is None:
            raise ValueError("Job has no output files")
        if remote_file_name not in self.output_file_names:
            raise KeyError(f"File with name {remote_file_name} does not exist for this job")
        local_file_name = self._job_queue_api.v1alpha_job_queue_jobs_id_outputsexport_get(
            id=self.id, file_name=remote_file_name
        )
        assert local_file_name
        with open(local_file_name, "rb") as f:
            return f.read()

    def update(self) -> None:
        """
        Update the job from the server.

        Raises
        ------
        ValueError
            If the job has been deleted from the server.
        """
        if self._is_deleted:
            raise ValueError("Job has been deleted from the Job Queue")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UndefinedObjectWarning)
            job_obj = self._job_queue_api.v1alpha_job_queue_jobs_id_get(id=self.id)
        assert job_obj
        self._update_job(job_obj)


@dataclass(frozen=True)
class JobQueueProcessingConfiguration:
    """Read only configuration of the Job Queue on the server."""

    purge_job_age_in_milliseconds: int
    purge_interval_in_milliseconds: int
    polling_interval_in_milliseconds: int
    concurrency: int
