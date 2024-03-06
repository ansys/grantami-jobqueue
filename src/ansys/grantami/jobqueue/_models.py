from abc import ABC, abstractmethod
from dataclasses import dataclass
import datetime
from enum import Enum
import json
import os
import pathlib
from typing import Any, Dict, List, Optional, Union
import warnings

from ansys.grantami.serverapi_openapi import api, models
from ansys.openapi.common import UndefinedObjectWarning, Unset


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


class _FileType(Enum):
    """Provides possible file types."""

    Attachment = "Attachment"
    Combined = "Combined"
    Data = "Data"
    Template = "Template"


@dataclass(frozen=True)
class ExportRecord:
    """Defines a record to be included in an Export job."""

    record_history_identity: int
    record_version: Optional[int] = None

    def to_dict(self) -> Dict[str, Union[int, None]]:
        """Serialize this object to a dictionary."""
        return {
            "RecordHistoryIdentity": self.record_history_identity,
            "RecordVersion": self.record_version,
        }


class _JobFile:
    def __init__(self, file_type: _FileType):
        self.file_type = file_type
        self._path: Union[pathlib.Path, None] = None
        self._id: Optional[str] = None

    @classmethod
    def from_pathlib_path(cls, path: pathlib.Path, file_type: _FileType) -> "_JobFile":
        new_obj = cls(file_type)
        new_obj.path = path
        return new_obj

    @classmethod
    def from_string(cls, file_path: str, file_type: _FileType) -> "_JobFile":
        path = pathlib.Path(file_path)
        new_obj = cls.from_pathlib_path(path, file_type)
        return new_obj

    @property
    def name(self) -> str:
        assert self._path
        return self._path.name

    @property
    def path(self) -> pathlib.Path:
        assert self._path
        return self._path

    @path.setter
    def path(self, value: pathlib.Path) -> None:
        self._path = value

    @property
    def serializable_path(self) -> str:
        assert self._path
        return str(self._path)

    @property
    def file_id(self) -> str:
        if not self._id:
            raise ValueError("File has not been uploaded to the server.")
        return self._id

    @file_id.setter
    def file_id(self, value: str) -> None:
        self._id = value


class JobRequest(ABC):
    """
    Abstract base class representing an job request.

    Each subclass represents a specific job type and may override some steps of the submission
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
        self.files: List[_JobFile] = []

    @abstractmethod
    def __repr__(self) -> str:
        """Printable representation of the object."""
        pass

    def _process_files(
        self, file_struct: Dict[_FileType, Optional[List[Union[str, pathlib.Path]]]]
    ) -> None:
        for file_type, file_list in file_struct.items():
            if file_list is None:
                continue
            for file in file_list:
                self._add_file(file, file_type)

    def _add_file(self, file_obj: Union[str, pathlib.Path], type_: _FileType) -> None:
        if isinstance(file_obj, pathlib.Path):
            new_file = _JobFile.from_pathlib_path(file_type=type_, path=file_obj)
        elif isinstance(file_obj, str):
            new_file = _JobFile.from_string(file_type=type_, file_path=file_obj)
        else:
            raise TypeError(
                "file_obj must be a pathlib.Path, BinaryIO, or str object. "
                f"Object provided was of type {type(file_obj)}."
            )
        self.files.append(new_file)

    def _post_files(self, api_client: api.JobQueueApi) -> None:
        for file in self.files:
            file_id = api_client.upload_file(file=file.path)
            file.file_id = file_id

    @abstractmethod
    def _render_job_parameters(self) -> str:
        """Serialize the parameters required to create the job.

        These are undocumented and vary depending on the specific job type.
        """
        pass

    def get_job_for_submission(self) -> models.GrantaServerApiAsyncJobsCreateJobRequest:
        """
        Create an AsyncJobs ``JobRequest`` object ready for submission to the job queue.

        Should be called after uploading files to the service.

        Returns
        -------
        JobRequest
            The JobRequest object to be submitted to the server.
        """
        job_parameters = self._render_job_parameters()
        job_request = models.GrantaServerApiAsyncJobsCreateJobRequest(
            type=self._job_type.value,
            name=self.name,
            description=self.description,
            scheduled_execution_date=self.scheduled_execution_date,
            input_file_ids=[file.file_id for file in self.files],
            parameters=job_parameters,
        )
        return job_request

    @property
    @abstractmethod
    def _job_type(self) -> JobType:
        pass

    @property
    def _file_types(self) -> List[_FileType]:
        return [file.file_type for file in self.files]


class ImportJobRequest(JobRequest, ABC):
    """
    Abstract base class representing an import job request.

    Each subclass represents a specific import job type and may override some steps of the submission
    process. They also add additional file types and properties as required.
    """

    def _process_files(
        self, file_struct: Dict[_FileType, Optional[List[Union[str, pathlib.Path]]]]
    ) -> None:
        """Check the validity of the file structure for importing.

        Required since only certain combinations of file types are permitted, and these combinations
        vary based on job type.
        """
        super()._process_files(file_struct=file_struct)
        self._check_files_valid_for_import()

    @abstractmethod
    def _check_files_valid_for_import(self) -> None:
        """
        Verify that the import job can run based on the combination of file types.

        Raises
        ------
        ValueError
            If not enough files have been provided for the job to successfully complete.

        """
        pass

    def _generate_file_list_for_import(self) -> List[Dict[str, str]]:
        file_params = []
        for file in self.files:
            file_params.append(
                {"fileType": file.file_type.value, "filePath": file.serializable_path}
            )
        return file_params

    def _render_job_parameters(self) -> str:
        file_params = self._generate_file_list_for_import()
        return json.dumps(file_params)

    @property
    @abstractmethod
    def _job_type(self) -> JobType:
        pass


class ExcelExportJobRequest(JobRequest):
    """
    Represents an Excel export job request.

    Requires both an Excel template and references to the records to be exported.

    Parameters
    ----------
    name
        The name of the job as displayed in the job queue.
    description
        The description of the job as displayed in the job queue.
    database_key
        The database key for the records to be exported.
    records
        The list of :class:`~.ExportRecord` objects representing the records to be exported.
    template_file
        Excel template file.
    scheduled_execution_date (optional)
        The earliest date and time the job should be executed.
    """

    def __init__(
        self,
        name: str,
        description: str,
        database_key: str,
        records: List[ExportRecord],
        template_file: Union[str, pathlib.Path],
        scheduled_execution_date: Optional[datetime.datetime] = None,
    ):
        super().__init__(name, description, scheduled_execution_date)
        self._database_key = database_key
        self._records = records
        self._process_files({_FileType.Template: [template_file]})

    def __repr__(self) -> str:
        """Printable representation of the object."""
        return f"<ExcelExportJobRequest '{self.name}'>"

    def _render_job_parameters(self) -> str:
        """
        Generate a serialized representation of the parameters required to create the export job.

        Includes references to the records to be exported and the name of the template file.
        """
        record_references = [r.to_dict() for r in self._records]
        assert self._file_types == [_FileType.Template]
        template_file = self.files[0].serializable_path
        parameters = {
            "DatabaseKey": self._database_key,
            "InputRecords": record_references,
            "TemplateFileName": template_file,
        }
        return json.dumps(parameters)

    @property
    def _job_type(self) -> JobType:
        return JobType.ExcelExportJob


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
        data_files: Optional[List[Union[str, pathlib.Path]]] = None,
        template_files: Optional[List[Union[str, pathlib.Path]]] = None,
        combined_files: Optional[List[Union[str, pathlib.Path]]] = None,
        attachment_files: Optional[List[Union[str, pathlib.Path]]] = None,
    ):
        super().__init__(name, description, scheduled_execution_date)
        self._process_files(
            {
                _FileType.Data: data_files,
                _FileType.Template: template_files,
                _FileType.Combined: combined_files,
                _FileType.Attachment: attachment_files,
            }
        )

    def __repr__(self) -> str:
        """Printable representation of the object."""
        return f"<ExcelImportJobRequest '{self.name}'>"

    def _check_files_valid_for_import(self) -> None:
        """
        Verify that the import job can run based on the provided files.

        If "Combined" files are provided, "Data" and "Template" files are not permitted. Otherwise,
        both "Data" and "Template" files must be provided.

        Raises
        ------
        ValueError
            If not enough files have been provided for the job to successfully complete.

        """
        if _FileType.Combined in self._file_types:
            if _FileType.Data in self._file_types or _FileType.Template in self._file_types:
                raise ValueError(
                    "Cannot create Excel import job with both combined and template/data files specified"
                )
        elif not (_FileType.Data in self._file_types and _FileType.Template in self._file_types):
            raise ValueError(
                "Excel import jobs must contain either a 'Combined' file or 'Data' files and a 'Template' file."
            )

    @property
    def _job_type(self) -> JobType:
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
        data_files: Optional[List[Union[str, pathlib.Path]]] = None,
        template_files: Optional[List[Union[str, pathlib.Path]]] = None,
        attachment_files: Optional[List[Union[str, pathlib.Path]]] = None,
    ):
        super().__init__(name, description, scheduled_execution_date)
        self._process_files(
            {
                _FileType.Data: data_files,
                _FileType.Template: template_files,
                _FileType.Attachment: attachment_files,
            }
        )

    def __repr__(self) -> str:
        """Printable representation of the object."""
        return f"<TextImportJobRequest '{self.name}'>"

    def _check_files_valid_for_import(self) -> None:
        """
        Verify that the import job can run based on the provided files.

        Both "Data" and "Template" files must be provided.

        Raises
        ------
        ValueError
            If not enough files have been provided for the job to successfully complete.

        """
        if not (_FileType.Data in self._file_types and _FileType.Template in self._file_types):
            raise ValueError(
                "Text import jobs must contain one or more 'Data' files and a 'Template' file"
            )

    @property
    def _job_type(self) -> JobType:
        return JobType.TextImportJob


class AsyncJob:
    """
    Represents a Job on the server.

    Provides information on the current status of the Job, as well as any job specific outputs.
    Allows modification of Job metadata, such as Name, Description and Scheduled Date.

    .. note::
        Do not instantiate this class directly. Objects of this type will be returned from
        :meth:`~JobQueueApiClient.create_job` and
        :meth:`~JobQueueApiClient.create_job_and_wait` methods.
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
        patch_resp = self._job_queue_api.update_job(id=self.id, body=patch_req)
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
        patch_resp = self._job_queue_api.update_job(id=self.id, body=patch_req)
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
        self._job_queue_api.move_to_top(id=self.id)
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
        patch_resp = self._job_queue_api.update_job(id=self.id, body=patch_req)
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
        downloaded_file_path = self._job_queue_api.get_job_output_file(
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
        local_file_name = self._job_queue_api.get_job_output_file(
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
            job_obj = self._job_queue_api.get_job(id=self.id)
        assert job_obj
        self._update_job(job_obj)


@dataclass(frozen=True)
class JobQueueProcessingConfiguration:
    """Read only configuration of the Job Queue on the server."""

    purge_job_age_in_milliseconds: int
    purge_interval_in_milliseconds: int
    polling_interval_in_milliseconds: int
    concurrency: int
