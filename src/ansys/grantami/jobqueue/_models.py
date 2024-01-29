import json
from typing import Dict, Optional, List, Union, IO, Tuple, TYPE_CHECKING
import pathlib
import datetime
from abc import ABC, abstractmethod
import os
import re

from ansys.grantami.serverapi_openapi import api, models

if TYPE_CHECKING:
    from ._connection import JobQueueApiClient


class ImportJobRequest(ABC):
    """
    Abstract base class representing an import job request. Each subclass represents a specific import type and may
    override some steps of the import process. They also add additional file types and properties as required.
    """

    @abstractmethod
    def __init__(
        self,
        name: str,
        description: str,
        scheduled_execution_date: datetime.datetime = None,
    ) -> None:
        """
        :param name: str (Display name of the job)
        :param description: str
        :param scheduled_execution_date: datetime.datetime (Earliest date and time job should be executed)

        :return: None
        """
        self.name = name
        self.description = description
        self.scheduled_execution_date = scheduled_execution_date
        self.files = {}  # type: Dict[str, Dict[str, Dict[str, Union[str, bytes]]]]
        self.__file_ids = []

    @abstractmethod
    def __repr__(self) -> str:
        pass

    def _process_files(self, file_struct: Dict[str, Optional[List[Union[str, pathlib.Path, IO]]]]) -> None:
        for file_type, file_list in file_struct.items():
            if file_list is not None:
                for file in file_list:
                    self._add_file(file, file_type)

    def _add_file(self, filepath_or_buffer: Union[str, pathlib.Path, IO], type_: str) -> None:
        file_name, file_contents = self.__read_file(filepath_or_buffer)
        if type_ not in self.files:
            self.files[type_] = {}
        self.files[type_][file_name] = {"contents": file_contents}

    @staticmethod
    def __read_file(filepath_or_buffer) -> Tuple[str, bytes]:
        if isinstance(filepath_or_buffer, (str, pathlib.Path)):
            with open(filepath_or_buffer, "rb") as f:
                file_contents = f.read()
                file_name = f.name
        else:
            file_contents = filepath_or_buffer.read()
            file_name = filepath_or_buffer.name
        return file_name, file_contents

    def _post_files(self, api_client: api.JobQueueApi):
        for file_type, file_list in self.files.items():
            for file_name, file_obj in file_list.items():
                file_id = api_client.v1alpha_job_queue_files_post(body=file_obj["contents"])
                file_obj["id"] = file_id
                file_obj["name"] = os.path.basename(file_name)
                self.__file_ids.append(file_id)

    def _generate_file_list_for_import(self):
        file_params = []
        for file_type, files in self.files.items():
            for file_obj in files.values():
                file_params.append({"fileType": file_type, "filePath": file_obj["name"]})
        return file_params

    def _render_file_parameters(self):
        file_params = self._generate_file_list_for_import()
        return json.dumps(file_params)

    def get_job_for_import(self) -> models.GrantaServerApiAsyncJobsCreateJobRequest:
        """
        Creates an AsyncJobs ``JobRequest`` object ready for import. Should be called after uploading
        files to the service.

        :return: AsyncJobs ``JobRequest`` object
        """
        scheduled_execution_date = self.scheduled_execution_date
        if scheduled_execution_date is not None:
            scheduled_execution_date = AsyncJob._format_timestamp(scheduled_execution_date)
        job_parameters = self._render_file_parameters()
        job_request =  models.GrantaServerApiAsyncJobsCreateJobRequest(
            type=self._import_type,
            name=self.name,
            description=self.description,
            scheduled_execution_date=scheduled_execution_date,
            input_file_ids=self.__file_ids,
            parameters=job_parameters,
        )
        return job_request

    @abstractmethod
    def check_valid_for_import(self) -> None:
        """
        Verifies that the import job can run. Raises a :class:`ValueError` with a specific error message if
        not enough files have been provided for the import to successfully complete.

        :return: None
        """
        pass

    @property
    @abstractmethod
    def _import_type(self):
        pass


class ExcelImportJobRequest(ImportJobRequest):
    """
    Represents an Excel import job request. Supports either combined imports (with template and data in the same file),
    or separate data and template imports.
    """

    def __init__(
        self,
        name: str,
        description: str,
        scheduled_execution_date: datetime.datetime = None,
        data_files: List[Union[str, pathlib.Path, IO]] = None,
        template_files: List[Union[str, pathlib.Path, IO]] = None,
        combined_files: List[Union[str, pathlib.Path, IO]] = None,
        attachment_files: List[Union[str, pathlib.Path, IO]] = None,
    ):
        """
        :param name: str (Display name of the job)
        :param description: str
        :param scheduled_execution_date: datetime.datetime (Earliest date and time job should be executed)
        :param data_files: List[Union[str, pathlib.Path, IO]] (Excel files containing data)
        :param template_files: List[Union[str, pathlib.Path, IO]] (Excel template files)
        :param combined_files: List[Union[str, pathlib.Path, IO]] (Excel files containing both template and data)
        :param attachment_files: List[Union[str, pathlib.Path, IO]] (Any other files referenced in data or combined
          Excel files)
        """
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
        return f"<ExcelImportJobRequest '{self.name}'>"

    def check_valid_for_import(self):
        if "Combined" in self.files:
            if "Data" in self.files or "Template" in self.files:
                raise ValueError("Cannot create Excel import job with both combined and template/data files specified")
        elif not ("Data" in self.files and "Template" in self.files):
            raise ValueError(
                "Excel import jobs must contain either a 'Combined' file or 'Data' files and a 'Template' file."
            )

    @property
    def _import_type(self):
        return "ExcelImportJob"


class TextImportJobRequest(ImportJobRequest):
    """
    Represents a Text import job request. Requires a template file and one or more data files.
    """

    def __init__(
        self,
        name: str,
        description: str,
        scheduled_execution_date: datetime.datetime = None,
        data_files: List[Union[str, pathlib.Path, IO]] = None,
        template_files: List[Union[str, pathlib.Path, IO]] = None,
        attachment_files: List[Union[str, pathlib.Path, IO]] = None,
    ):
        """
        :param name: str (Display name of the job)
        :param description: str
        :param scheduled_execution_date: datetime.datetime (Earliest date and time job should be executed)
        :param data_files: List[Union[str, pathlib.Path, IO]] (Text files containing data)
        :param template_files: List[Union[str, pathlib.Path, IO]] (Text importer template file)
        :param attachment_files: List[Union[str, pathlib.Path, IO]] (Any other files referenced in data files)
        """
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
        return f"<TextImportJobRequest '{self.name}'>"

    def check_valid_for_import(self):
        if not ("Data" in self.files and "Template" in self.files):
            raise ValueError("Text import jobs must contain 'Data' files and a 'Template' file")

    @property
    def _import_type(self):
        return "TextImportJob"


class AsyncJob:
    """
    Represents a Job on the server. Provides information on the current status of the Job, as well as any
    job specific outputs. Allows modification of Job metadata, such as Name, Description and Scheduled Date.
    """

    def __init__(self):
        self.__json_obj = None
        self.__job_queue_api = None
        self.__is_deleted = False

    def __repr__(self) -> str:
        return f"<AsyncJob '{self.name}' status '{self.status}'>"

    @property
    def id(self) -> str:
        """
        Unique job identifier in GUID form. Recommended way to refer to individual jobs.

        :return: str
        """
        return self.__json_obj.id

    @property
    def name(self) -> str:
        """
        Display name of the job (not unique).

        :return: str
        """
        return self.__json_obj.name

    def update_name(self, value: str) -> None:
        """
        Updates the display name of the job on the server.

        :param value: str

        :return: None
        """
        if self.__is_deleted:
            raise ValueError("Job has been deleted from the Job Queue")
        patch_req = self.__json_obj
        patch_req.name = value
        patch_resp = self.__job_queue_api.v1alpha_job_queue_jobs_id_patch(id=self.id, body=patch_req)
        self._update_job(patch_resp)

    @property
    def description(self) -> str:
        """
        Description of the job (displayed in MI).

        :return: str
        """
        return self.__json_obj.description

    def update_description(self, value: str) -> None:
        """
        Updates the job description on the server.

        :param value: str

        :return: None
        """
        if self.__is_deleted:
            raise ValueError("Job has been deleted from the Job Queue")
        patch_req = self.__json_obj
        patch_req.description = value
        patch_resp = self.__job_queue_api.v1alpha_job_queue_jobs_id_patch(id=self.id, body=patch_req)
        self._update_job(patch_resp)

    @property
    def status(self) -> str:
        """
        Job status on the server:

        * ``Pending``: Job is in the queue
        * ``Running``: Job is currently executing
        * ``Succeeded``: Job has completed (does not guarantee that no errors occurred)
        * ``Failed``: Job could not complete
        * ``Cancelled``: Job was cancelled by the user
        * ``Corrupted``: Something went wrong on the server

        If the job associated with the :obj:`AsyncJob` object was deleted, returns ``Deleted``.

        :return: str
        """
        if self.__is_deleted:
            return "Deleted"
        return self.__json_obj.status

    @property
    def type(self) -> str:
        """
        Job type, as known to the server.

        :return: str
        """
        return self.__json_obj.type

    @property
    def position(self) -> Union[int, None]:
        """
        Position in the Job Queue. Returns an ``int`` if the job is pending, otherwise returns ``None``.

        :return: int or None
        """
        return self.__json_obj.position

    def move_to_top(self) -> None:
        """
        Promotes the job to the top of the Job Queue. User must have MI_ADMIN permission.

        :return: None
        """
        self.__job_queue_api.v1alpha_job_queue_jobs_idmove_to_top_post(id=self.id)
        self.update()

    @property
    def submitter_information(
        self,
    ) -> Dict[str, Union[str, datetime.datetime, List[str]]]:
        """
        Information about the job submission. Returns the ``username`` of the submitter, ``date_time`` of submission,
        and the ``roles`` to which the submitter belongs as a dictionary indexed by name.

        :return: dict
        """
        return {
            "username": self.__json_obj.submitter_name,
            "date_time": AsyncJob._format_datetime(self.__json_obj.submission_date),
            "roles": self.__json_obj.submitter_roles,
        }

    @property
    def completion_date_time(self) -> Optional[datetime.datetime]:
        """
        Date and time of job completion. Returns ``None`` if job is pending.

        :return: datetime.datetime or None
        """
        return AsyncJob._format_datetime(self.__json_obj.completion_date)

    @property
    def execution_date_time(self) -> Optional[datetime.datetime]:
        """
        Date and time of job execution. Returns ``None`` if job is pending.

        :return: datetime.datetime or None
        """
        return AsyncJob._format_datetime(self.__json_obj.execution_date)

    @property
    def scheduled_execution_date_time(self) -> Optional[datetime.datetime]:
        """
        Date and time of job execution, if scheduled.

        :return: datetime.datetime or None
        """
        return AsyncJob._format_datetime(self.__json_obj.scheduled_execution_date)

    def update_scheduled_execution_date_time(self, value: datetime.datetime) -> None:
        """
        Updates the scheduled execution time on the server.

        :param value: datetime.datetime

        :return: None
        """
        if self.__is_deleted:
            raise ValueError("Job has been deleted from the Job Queue")
        patch_req = self.__json_obj
        patch_req.scheduled_execution_date = AsyncJob._format_timestamp(value)
        patch_resp = self.__job_queue_api.v1alpha_job_queue_jobs_id_patch(id=self.id, body=patch_req)
        self._update_job(patch_resp)

    @property
    def output_information(self):
        """
        Provides additional information such as record placement or verbose logging, if the job type supports
        it.

        :return: Any job-specific outputs
        """
        return self.__json_obj.job_specific_outputs

    @property
    def output_file_names(self) -> List[str]:
        """
        List of file names produced by the job, for example log files.

        :return: List[str]
        """
        return self.__json_obj.output_file_names

    def download_file(self, remote_file_name: str, file_path: Union[str, pathlib.Path]) -> None:
        """
        Downloads an output file from the server by name and saves it to a specified location.

        :param remote_file_name: str (File name provided by :meth:`output_file_names`)
        :param file_path: :obj:`pathlib.Path` or str (Path where the file should be saved; if a file name isn't
          specified, the name provided by :meth:`output_file_names` is used)

        :return: None
        """

        if self.__is_deleted:
            raise ValueError("Job has been deleted from the Job Queue")
        if remote_file_name not in self.output_file_names:
            raise KeyError(f"File with name {remote_file_name} does not exist for this job")
        file_content = self.__job_queue_api.v1alpha_job_queue_jobs_id_outputsexport_get(
            id=self.id,
            file_name=remote_file_name
        )
        if isinstance(file_path, str):
            file_path = pathlib.Path(file_path)
        if file_path.is_dir():
            remote_name = pathlib.Path(remote_file_name).name
            file_path = file_path / remote_name
        if isinstance(file_content, bytes):
            with file_path.open(mode="wb") as f:
                f.write(file_content)
        else:
            with file_path.open(mode="w") as f:
                if isinstance(file_content, str):
                    f.write(file_content)
                else:
                    json.dump(file_content, f)

    def get_file_content(self, remote_file_name: str) -> Optional[bytes]:
        """
        Downloads an output file from the server by name, and returns the file contents.

        :param remote_file_name: str (File name provided by :meth:`output_file_names`)

        :return: Union[bytes, str, dict]
        """
        if self.__is_deleted:
            raise ValueError("Job has been deleted from the Job Queue")
        if remote_file_name not in self.output_file_names:
            raise KeyError(f"File with name {remote_file_name} does not exist for this job")
        return self.__job_queue_api.v1alpha_job_queue_jobs_id_outputsexport_get(
            id=self.id,
            file_name=remote_file_name
        )

    def update(self) -> None:
        """
        Updates the job from the server.

        :return: None
        """
        if self.__is_deleted:
            raise ValueError("Job has been deleted from the Job Queue")
        job_resp = self.__job_queue_api.v1alpha_job_queue_jobs_id_get(id=self.id)
        self._update_job(job_resp)

    def _update_job(self, job_obj: models.GrantaServerApiAsyncJobsJob) -> None:
        self.__json_obj = job_obj

    @classmethod
    def _init_from_obj(
        cls,
        job_obj: models.GrantaServerApiAsyncJobsJob,
        client: "JobQueueApiClient",
    ) -> "AsyncJob":
        new = cls()
        new.__job_queue_api = client.job_queue_api
        new._update_job(job_obj)
        return new

    @staticmethod
    def _format_datetime(date_string: Optional[str]) -> Optional[datetime.datetime]:
        if date_string is None:
            return None
        date_int_search = re.search(r"/Date\((-?[\d]+)\)", date_string)
        if date_int_search:
            date_str = date_int_search.group(1)
            date_int = int(date_str[:-3])
            if date_int < 0:
                return None
            return datetime.datetime.utcfromtimestamp(date_int)
        raise ValueError("Invalid date object in response json")

    @staticmethod
    def _format_timestamp(date_time: datetime.datetime) -> str:
        timestamp = date_time.replace(tzinfo=datetime.timezone.utc).timestamp()
        epoch = str(int(timestamp * 1000))
        return f"/Date({epoch})/"
