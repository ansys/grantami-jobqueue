# Copyright (C) 2024 - 2025 ANSYS, Inc. and/or its affiliates.
# SPDX-License-Identifier: MIT
#
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""Module for connections."""
import time
from typing import Dict, List, Optional, Tuple, cast
import warnings

from ansys.grantami.serverapi_openapi.v2025r2 import api, models
from ansys.openapi.common import (
    ApiClient,
    ApiClientFactory,
    ApiException,
    SessionConfiguration,
    UndefinedObjectWarning,
    generate_user_agent,
)
import requests  # type: ignore[import-untyped]

from ._logger import logger
from ._models import AsyncJob, JobQueueProcessingConfiguration, JobRequest, JobStatus, JobType

PROXY_PATH = "/proxy/v1.svc/mi"
AUTH_PATH = "/Health/v2.svc"
API_DEFINITION_PATH = "/swagger/v1/swagger.json"
GRANTA_APPLICATION_NAME_HEADER = "PyGranta JobQueue"

MINIMUM_GRANTA_MI_VERSION = (24, 2)

_ArgNotProvided = "_ArgNotProvided"


def _get_mi_server_version(client: ApiClient) -> Tuple[int, ...]:
    """
    Get the Granta MI version as a tuple.

    This method makes direct use of the underlying ``serverapi-openapi`` package.
    The API methods in this package may change over time, and so this method is expected
    to grow to support multiple versions of the ``serverapi-openapi`` package.

    Parameters
    ----------
    client : :class:`~.RecordListApiClient`
        Client object.

    Returns
    -------
    tuple of int
        Granta MI version number.
    """
    schema_api = api.SchemaApi(client)
    server_version_response = schema_api.get_version()
    assert server_version_response.version
    server_version_elements = server_version_response.version.split(".")
    server_version = tuple([int(e) for e in server_version_elements])
    return server_version


class JobQueueApiClient(ApiClient):
    """
    Communicates with Granta MI.

    This class is instantiated by the :class:`Connection` class
    and should not be instantiated directly.
    """

    def __init__(
        self,
        session: requests.Session,
        service_layer_url: str,
        configuration: SessionConfiguration,
    ) -> None:
        self._service_layer_url = service_layer_url
        api_url = service_layer_url + PROXY_PATH

        logger.debug("Creating JobQueueApiClient")
        logger.debug(f"Base Service Layer URL: {self._service_layer_url}")
        logger.debug(f"Service URL: {api_url}")

        super().__init__(session, api_url, configuration)
        self.job_queue_api = api.JobQueueApi(self)

        self._user: Optional[models.GsaCurrentUser] = None
        self._processing_configuration: Optional[JobQueueProcessingConfiguration] = None

        self._jobs: Dict[str, AsyncJob] = {}

        self._wait_retries = 5

    def __repr__(self) -> str:
        """Printable representation of the object."""
        return f"<{self.__class__.__name__} url: {self._service_layer_url}>"

    @property
    def processing_configuration(self) -> JobQueueProcessingConfiguration:
        """
        Current job queue configuration information from the server.

        Performs an HTTP request against the Granta MI Server API.

        Returns
        -------
        JobQueueProcessingConfiguration
            Current job queue processing configuration on the server.
        """
        if self._processing_configuration is None:
            processing_config = self.job_queue_api.get_processing_config()
            self._processing_configuration = JobQueueProcessingConfiguration(
                purge_job_age_in_milliseconds=cast(
                    int, processing_config.purge_job_age_in_milliseconds
                ),
                purge_interval_in_milliseconds=cast(
                    int, processing_config.purge_interval_in_milliseconds
                ),
                polling_interval_in_milliseconds=cast(
                    int, processing_config.polling_interval_in_milliseconds
                ),
                concurrency=cast(int, processing_config.concurrency),
            )
        return self._processing_configuration

    @property
    def is_admin_user(self) -> bool:
        """
        Flag indicating if the current user is an administrator of the job queue.

        Administrators can promote jobs to the top of the queue and interact with other users' jobs.

        Performs an HTTP request against the Granta MI Server API.

        Returns
        -------
        bool
            ``True`` if the user is an administrator, ``False`` otherwise.
        """
        if self._user is None:
            self._refetch_user()
        assert self._user
        return cast(bool, self._user.is_admin)

    @property
    def can_write_job(self) -> bool:
        """
        Flag indicating if the current user can create jobs.

        Performs an HTTP request against the Granta MI Server API.

        Returns
        -------
        bool
            ``True`` if the user can create jobs, ``False`` otherwise.
        """
        if self._user is None:
            self._refetch_user()
        assert self._user
        return cast(bool, self._user.has_write_access)

    @property
    def num_jobs(self) -> int:
        """
        Number of jobs in the job queue, including completed and failed jobs.

        Performs an HTTP request against the Granta MI Server API.

        Returns
        -------
        int
            Number of jobs in the job queue.
        """
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UndefinedObjectWarning)
            jobs = self.job_queue_api.get_jobs()
        return len(cast(List[models.GsaJob], jobs.results))

    def _refetch_user(self) -> None:
        """Refetch the current user information from the server."""
        self._user = self.job_queue_api.get_current_user()
        assert self._user

    @property
    def jobs(self) -> "List[AsyncJob]":
        """
        List of all jobs on the server visible to the current user.

        Running or pending jobs are sorted according to their positions in the queue.
        Completed or failed jobs are returned last.

        Performs an HTTP request against the Granta MI Server API.

        Returns
        -------
        list[AsyncJob]
            List of all jobs on the server visible to the current user.
        """
        self._refetch_jobs()
        return sorted(self._jobs.values(), key=lambda x: (x.position is None, x.position))

    def jobs_where(
        self,
        name: Optional[str] = None,
        job_type: Optional[JobType] = None,
        description: Optional[str] = None,
        submitter_name: Optional[str] = None,
        status: Optional[JobStatus] = None,
    ) -> "List[AsyncJob]":
        """
        Get a list of jobs on the server matching a query.

        Running or queued jobs are sorted according to their positions in the queue.
        Completed or failed jobs are returned last.

        Performs an HTTP request against the Granta MI Server API.

        Parameters
        ----------
        name : str, default: None
            Text that must appear in the job name.
        job_type : JobType, default: None
            Type of job to search for.
        description : str, default: None
            Text that must appear in the job description.
        submitter_name : str, default: None
            Text that must equal the name of the user who submitted the job.
        status : JobStatus, default: None
            Status of the job.

        Returns
        -------
        list of AsyncJob
            List of jobs on the server matching the query.
        """
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UndefinedObjectWarning)
            filtered_job_resp = self.job_queue_api.get_jobs(
                name_filter=name,
                job_type=job_type.value if job_type else None,
                status=status.value if status else None,
                description_filter=description,
                submitter_name_filter=submitter_name,
            )

        job_list = filtered_job_resp.results
        assert isinstance(job_list, list)
        self._update_job_list_from_resp(job_resp=job_list)
        if not filtered_job_resp.results:
            return []
        filtered_ids = [job.id for job in filtered_job_resp.results]
        return [job for id_, job in self._jobs.items() if id_ in filtered_ids]

    def get_job_by_id(self, job_id: str) -> "AsyncJob":
        """
        Get the job with a given job ID.

        Parameters
        ----------
        job_id : str
            Job ID.

        Returns
        -------
        AsyncJob
            Job with the given ID.
        """
        return next(job for id_, job in self._jobs.items() if id_ == job_id)

    def delete_jobs(self, jobs: "List[AsyncJob]") -> None:
        """
        Delete one or more jobs from the server.

        Parameters
        ----------
        jobs : list of AsyncJob
            List of jobs to delete from the server.
        """
        for job in jobs:
            self.job_queue_api.delete_job(id=job.id)
            self._jobs.pop(job.id, None)
            job._is_deleted = True
        self._refetch_jobs()

    def _refetch_jobs(self) -> None:
        """Refetch the list of jobs from the server."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UndefinedObjectWarning)
            job_resp = self.job_queue_api.get_jobs()
        job_list = job_resp.results
        assert isinstance(job_list, list)
        self._update_job_list_from_resp(job_resp=job_list, flush_jobs=True)

    def _update_job_list_from_resp(
        self, job_resp: List[models.GsaJob], flush_jobs: bool = False
    ) -> None:
        """
        Update the internal job list with a list of job objects from the server.

        Parameters
        ----------
        job_resp : List[models.GsaJob]
            List of job objects from the server.
        flush_jobs : bool, default: False
            Whether to remove jobs from the internal list that are not in
            the ``job_resp`` list.
        """
        remote_ids = [remote_job.id for remote_job in job_resp]
        if flush_jobs:
            for job_id in self._jobs:
                if job_id not in remote_ids:
                    self._jobs.pop(job_id)
        for job_obj in job_resp:
            job_id = cast(str, job_obj.id)
            if job_id not in self._jobs:
                self._jobs[job_id] = AsyncJob.create_job(job_obj, self.job_queue_api)
            elif job_obj is not self._jobs[job_id]:
                self._jobs[job_id]._update_job(job_obj)

    def create_job_and_wait(self, job_request: "JobRequest") -> "AsyncJob":  # noqa: D205, D400
        """
        Create a job from an Excel import or export request or from a text import request.

        This method create a job from an :class:`~.ExcelImportJobRequest`, :class:`~.ExcelExportJobRequest`, or
        :class:`~.TextImportJobRequest` object and waits until the job is complete.

        This method also uploads the files included in the job request as a part of the job
        submission process.

        Parameters
        ----------
        job_request : JobRequest
            Job request to submit to the job queue.

        Returns
        -------
        AsyncJob
            Object representing the completed job.
        """
        job = self.create_job(job_request=job_request)
        request_count = 0
        last_exception: Optional[Exception] = None
        time.sleep(1)
        while request_count < self._wait_retries:
            try:
                job.update()
                status = job.status
                if status not in [JobStatus.Pending, JobStatus.Running]:
                    return job
            except ApiException as exception_info:
                request_count += 1
                last_exception = exception_info
            except Exception as exception_info:
                last_exception = exception_info
                break
            time.sleep(1)
        if last_exception:
            raise last_exception
        else:
            return job

    def create_job(self, job_request: "JobRequest") -> "AsyncJob":  # noqa: D205, D400
        """
        Create a job from an Excel import or export request or from a text import request.

        This method creates a job from an :class:`~.ExcelImportJobRequest`, :class:`~.ExcelExportJobRequest`, or
        :class:`~.TextImportJobRequest` object.

        This method also uploads the files included in the job request as a part of the job
        submission process.

        Parameters
        ----------
        job_request : JobRequest
            Job request to submit to the server.

        Returns
        -------
        AsyncJob
            Object representing the in-progress job.
        """
        job_request._post_files(api_client=self.job_queue_api)

        job_response = self.job_queue_api.create_job(body=job_request._get_job_for_submission())
        self._update_job_list_from_resp([job_response])
        return self._jobs[cast(str, job_response.id)]


class Connection(ApiClientFactory):
    """
    Connects to a Granta MI Server API instance.

    This is a subclass of the :class:`ansys.openapi.common.ApiClientFactory` class. All methods in
    this class are documented as returning :class:`~ansys.openapi.common.ApiClientFactory` class
    instances of the :class:`ansys.grantami.jobqueue.Connection` class.

    Parameters
    ----------
    servicelayer_url : str
       Base URL of the Granta MI Service Layer application.
    session_configuration : :class:`~ansys.openapi.common.SessionConfiguration`, default: None
       Additional configuration settings for the requests session. If ``None``, the
       :class:`~ansys.openapi.common.SessionConfiguration` class with default parameters
       is used.

    Notes
    -----
    For advanced usage, including configuring session-specific properties and timeouts, see the
    :external+openapi-common:doc:`OpenAPI-Common API reference documentation <api/index>`.
    Specifically, see the documentation for the :class:`~ansys.openapi.common.ApiClientFactory`
    base class and the :class:`~ansys.openapi.common.SessionConfiguration` class.

    1. Create the connection builder object and specify the server to connect to.
    2. Specify the authentication method to use for the connection and provide credentials if
       required.
    3. Connect to the server, which returns the client object.

    The examples show this process for different authentication methods.

    Examples
    --------
    >>> client = Connection("http://my_mi_server/mi_servicelayer").with_autologon().connect()
    >>> client
    <JobQueueApiClient: url=http://my_mi_server/mi_servicelayer>

    >>> client = (
    ...     Connection("http://my_mi_server/mi_servicelayer")
    ...     .with_credentials(username="my_username", password="my_password")
    ...     .connect()
    ... )
    >>> client
    <JobQueueApiClient: url: http://my_mi_server/mi_servicelayer>
    """

    def __init__(
        self, servicelayer_url: str, session_configuration: Optional[SessionConfiguration] = None
    ):
        from . import __version__

        auth_url = servicelayer_url.strip("/") + AUTH_PATH
        super().__init__(auth_url, session_configuration)
        self._base_service_layer_url = servicelayer_url
        self._session_configuration.headers["X-Granta-ApplicationName"] = (
            GRANTA_APPLICATION_NAME_HEADER
        )
        self._session_configuration.headers["User-Agent"] = generate_user_agent(
            "ansys-grantami-jobqueue", __version__
        )

    def connect(self) -> JobQueueApiClient:
        """
        Finalize the :class:`.JobQueueApiClient` client and return it for use.

        Authentication must be configured for this method to succeed.

        Returns
        -------
        :class:`.JobQueueApiClient`
            Client object that can be used to connect to Granta MI and interact with the job queue
            API.
        """
        self._validate_builder()
        client = JobQueueApiClient(
            self._session,
            self._base_service_layer_url,
            self._session_configuration,
        )
        client.setup_client(models)
        self._test_connection(client)
        return client

    @staticmethod
    def _test_connection(client: JobQueueApiClient) -> None:
        """
        Check if the created client can be used to perform a request.

        This method tests both that the API definition can be accessed and that the Granta MI
        version is compatible with this package.

        The first checks ensures that the Server API exists and is functional. The second check
        ensures that the Granta MI server version is compatible with this version of the package.

        A failure at any point raises a ``ConnectionError``.

        Parameters
        ----------
        client : :class:`~.JobQueueApiClient`
            Client object to test.

        Raises
        ------
        ConnectionError
            Error raised if the connection test fails.
        """
        try:
            client.call_api(resource_path=API_DEFINITION_PATH, method="GET")
        except ApiException as e:
            if e.status_code == 404:
                raise ConnectionError(
                    "Cannot find the Server API definition in the Granta MI Service Layer. Ensure "
                    "that a compatible version of Granta MI is available and try again."
                ) from e
            else:
                raise ConnectionError(
                    "An unexpected error occurred when trying to connect to the Server API in the Granta "
                    " MI Service Layer. Check the Service Layer logs for more information and try "
                    "again."
                ) from e
        except requests.exceptions.RetryError as e:
            raise ConnectionError(
                "An unexpected error occurred when trying to connect to the Granta MI Server API. Check "
                "that SSL certificates have been configured for communications between the Granta MI "
                "Server and client Granta MI applications."
            ) from e

        try:
            server_version = _get_mi_server_version(client)
        except ApiException as e:
            raise ConnectionError(
                "Cannot check the Granta MI server version. Ensure that the Granta MI server version "
                f"is at least {'.'.join([str(e) for e in MINIMUM_GRANTA_MI_VERSION])}."
            ) from e

        # Once there are multiple versions of this package targeting different Granta MI server
        # versions, the error message should direct users towards the PyGranta metapackage for
        # earlier versions. This is not necessary now though, because there is no support for
        # versions earlier than 2023 R2.

        if server_version < MINIMUM_GRANTA_MI_VERSION:
            raise ConnectionError(
                f"This package requires a more recent Granta MI version. Detected Granta MI server "
                f"version is {'.'.join([str(e) for e in server_version])}, but this package "
                f"requires at least {'.'.join([str(e) for e in MINIMUM_GRANTA_MI_VERSION])}."
            )
