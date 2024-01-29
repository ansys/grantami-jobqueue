from typing import Dict, List, Optional, Tuple, Union
import time

from ansys.grantami.serverapi_openapi import api, models  # type: ignore[import]
from ansys.openapi.common import (  # type: ignore[import]
    ApiClient,
    ApiClientFactory,
    ApiException,
    SessionConfiguration,
    generate_user_agent,
)
import requests  # type: ignore[import]

from ._logger import logger
from ._models import AsyncJob, ImportJobRequest

PROXY_PATH = "/proxy/v1.svc"
AUTH_PATH = "/Health/v2.svc"
API_DEFINITION_PATH = "/swagger/v1/swagger.json"
GRANTA_APPLICATION_NAME_HEADER = "PyGranta JobQueue"

MINIMUM_GRANTA_MI_VERSION = (24, 1)

_ArgNotProvided = "_ArgNotProvided"


def _get_mi_server_version(client: ApiClient) -> Tuple[int, ...]:
    """Get the Granta MI version as a tuple.

    Makes direct use of the underlying serverapi-openapi package. The API methods
    in this package may change over time, and so it is expected that this method
    will grow to support multiple versions of the serverapi-openapi package.

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
    server_version_response = schema_api.v1alpha_schema_mi_version_get()
    server_version_elements = server_version_response.version.split(".")
    server_version = tuple([int(e) for e in server_version_elements])
    return server_version


class JobQueueApiClient(ApiClient):  # type: ignore[misc]
    """
    Communicates with Granta MI.

    This class is instantiated by the
    :class:`Connection` class and should not be instantiated
    directly.
    """

    def __init__(
        self,
        session: requests.Session,
        service_layer_url: str,
        configuration: SessionConfiguration,
    ):
        self._service_layer_url = service_layer_url
        api_url = service_layer_url + PROXY_PATH

        logger.debug("Creating JobQueueApiClient")
        logger.debug(f"Base Service Layer URL: {self._service_layer_url}")
        logger.debug(f"Service URL: {api_url}")

        super().__init__(session, api_url, configuration)
        self.job_queue_api = api.JobQueueApi(self)

        self._user = None
        self._processing_configuration = None

        self._jobs = {}

        self.__import_job_type_map = {
            "Excel": "ExcelImportJob",
            "Text": "TextImportJob",
        }

        self.__valid_status_ids = [
            "Pending",
            "Running",
            "Succeeded",
            "Failed",
            "Cancelled",
            "Corrupted",
        ]

        self._wait_retries = 5

    def __repr__(self) -> str:
        """Printable representation of the object."""
        return f"<{self.__class__.__name__} url: {self._service_layer_url}>"

    @property
    def processing_configuration(self) -> Dict[str, int]:
        """
        Gets the current job queue configuration information from the server.

        :return: dict
        """
        if self._processing_configuration is None:
            self._processing_configuration = self.job_queue_api.v1alpha_job_queue_processing_configuration_get()
        return self._processing_configuration

    @property
    def is_admin_user(self) -> bool:
        """
        Checks whether the current user is a Job Queue admin (returns ``True`` if the user is an admin). Admin users
        can promote jobs to the top of the queue and interact with other users' jobs.

        :return: bool
        """
        if self._user is None:
            self._refetch_user()
        return self._user.is_admin

    @property
    def can_write_job(self) -> bool:
        """
        Checks whether the current user can create new jobs (returns ``True`` if they can).

        :return: bool
        """
        if self._user is None:
            self._refetch_user()
        return self._user.has_write_access

    @property
    def num_jobs(self) -> int:
        """
        Returns the number of jobs in the Job Queue, including completed and failed jobs.

        :return: int
        """
        jobs = self.job_queue_api.v1alpha_job_queue_jobs_get()
        return len(jobs.results)

    def _refetch_user(self) -> None:
        self._user = self.job_queue_api.get_currentuser()

    @property
    def jobs(self) -> "List[AsyncJob]":
        """
        Returns a list of all jobs visible on the server. Running or pending jobs are sorted according to
        their position in the queue, completed or failed jobs are returned last.

        :return: List[:class:`AsyncJob`]
        """
        self._refetch_jobs()
        return sorted(self._jobs.values(), key=lambda x: (x.position is None, x.position))

    def jobs_where(
            self,
            name: str = None,
            type_: str = None,
            description: str = None,
            submitter_name: str = None,
            status: str = None,
    ) -> "List[AsyncJob]":
        """
        Returns a list of jobs on the server matching a query. Running or queued jobs are sorted according to
        their position in the queue, completed or failed jobs are returned last.

        :param name: str (Job name must contain)
        :param type_: str (``Excel``, ``Text``)
        :param description: str (Job description must contain)
        :param submitter_name: str (Name of user who submitted the job must equal)
        :param status: str (``Pending``, ``Running``, ``Succeeded``, ``Failed``, ``Cancelled``, ``Corrupted``)

        :return: List[:class:`AsyncJob`]
        """
        if type_ is not None and type_ not in self.__import_job_type_map:
            valid_job_types = ", ".join(self.__import_job_type_map.keys())
            raise ValueError(f"Invalid job type '{type_}', must be one of: {valid_job_types}")
        if status is not None and status not in self.__valid_status_ids:
            valid_status_ids = ", ".join(self.__valid_status_ids)
            raise ValueError(f"Invalid status '{status}', must be one of: {valid_status_ids}")

        kwargs = {
            "name_filter": name,
            "job_type": type_,
            "status": status,
            "description_filter": description,
            "submitter_name_filter": submitter_name,
        }

        filtered_job_resp = self.job_queue_api.v1alpha_job_queue_jobs_get(
            **{k: v for k, v in kwargs.items() if v is not None})

        self._update_job_list_from_resp(job_resp=filtered_job_resp.results)
        filtered_ids = [job.id for job in filtered_job_resp.results]
        return [job for id_, job in self._jobs.items() if id_ in filtered_ids]

    def get_job_by_id(self, job_id: str) -> "AsyncJob":
        """
        Gets the job with unique identifier ``job_id`` from the server.

        :param job_id: str

        :return: :class:`AsyncJob` object
        """
        return next(job for id_, job in self._jobs.items() if id_ == job_id)

    def delete_jobs(self, jobs: "List[AsyncJob]") -> None:
        """
        Deletes jobs from the server.

        :param jobs: List[:class:`AsyncJob`]

        :return: None
        """
        for job in jobs:
            self.job_queue_api.v1alpha_job_queue_jobs_id_delete(id=job.id)
            self._jobs.pop(job.id, None)
            job._AsyncJob__is_deleted = True
        self._refetch_jobs()

    def _refetch_jobs(self) -> None:
        job_list = self.job_queue_api.v1alpha_job_queue_jobs_get()
        self._update_job_list_from_resp(job_resp=job_list.results, flush_jobs=True)

    def _update_job_list_from_resp(self, job_resp, flush_jobs=False) -> None:
        remote_ids = [remote_job.id for remote_job in job_resp]
        if flush_jobs:
            for job_id in self._jobs:
                if job_id not in remote_ids:
                    self._jobs.pop(job_id)
        for job_obj in job_resp:
            if job_obj.id not in self._jobs:
                self._jobs[job_obj.id] = AsyncJob._init_from_obj(job_obj, self)
            elif job_obj is not self._jobs[job_obj.id]:
                self._jobs[job_obj.id]._update_job(job_obj)

    def create_import_job_and_wait(self, job_request: "ImportJobRequest") -> "AsyncJob":
        """
        Creates an import job from an :obj:`ImportJobRequest` object. Uploads files and submits a job request
        to the Job Queue. Blocks execution until the job has either completed or failed, then returns the finished
        :obj:`AsyncJob` object.

        :param job_request: :obj:`ImportJobRequest` object

        :return: :obj:`AsyncJob` object
        """
        job = self.create_import_job(job_request=job_request)
        request_count = 0
        last_exception = None
        time.sleep(1)
        while request_count < self._wait_retries:
            try:
                job.update()
                status = job.status
                if status not in ["Pending", "Running"]:
                    return job
            except ApiException as exception_info:
                request_count += 1
                last_exception = exception_info
            except Exception as exception_info:
                last_exception = exception_info
                break
            time.sleep(1)
        raise last_exception

    def create_import_job(self, job_request: "ImportJobRequest") -> "AsyncJob":
        """
        Creates an import job from an :obj:`ImportJobRequest` object. Uploads files and submits a job request
        to the Job Queue, then returns an in-progress :obj:`AsyncJob` object for later use.

        :param job_request: :obj:`ImportJobRequest` object

        :return: :obj:`AsyncJob` object
        """
        job_request._post_files(api_client=self.job_queue_api)

        job_response = self.job_queue_api.v1alpha_job_queue_jobs_post(body=job_request.get_job_for_import())
        self._update_job_list_from_resp([job_response])
        return self._jobs[job_response.id]


class Connection(ApiClientFactory):  # type: ignore[misc]
    """
    Connects to a Granta MI ServerAPI instance.

    This is a subclass of the :class:`ansys.openapi.common.ApiClientFactory` class. All methods in
    this class are documented as returning :class:`~ansys.openapi.common.ApiClientFactory` class
    instances of the :class:`ansys.grantami.recordlists.Connection` class instead.

    Parameters
    ----------
    servicelayer_url : str
       Base URL of the Granta MI Service Layer application.
    session_configuration : :class:`~ansys.openapi.common.SessionConfiguration`, optional
       Additional configuration settings for the requests session. The default is ``None``, in which
       case the :class:`~ansys.openapi.common.SessionConfiguration` class with default parameters
       is used.

    Notes
    -----
    For advanced usage, including configuring session-specific properties and timeouts, see the
    :external+openapi-common:doc:`ansys-openapi-common API reference <api/index>`. Specifically, see
    the documentation for the :class:`~ansys.openapi.common.ApiClientFactory` base class and the
    :class:`~ansys.openapi.common.SessionConfiguration` class


    1. Create the connection builder object and specify the server to connect to.
    2. Specify the authentication method to use for the connection and provide credentials if
       required.
    3. Connect to the server, which returns the client object.

    The examples show this process for different authentication methods.

    Examples
    --------
    >>> client = Connection("http://my_mi_server/mi_servicelayer").with_autologon().connect()
    >>> client
    <RecordListsApiClient: url=http://my_mi_server/mi_servicelayer>
    >>> client = (
    ...     Connection("http://my_mi_server/mi_servicelayer")
    ...     .with_credentials(username="my_username", password="my_password")
    ...     .connect()
    ... )
    >>> client
    <RecordListsApiClient: url: http://my_mi_server/mi_servicelayer>
    """

    def __init__(
        self, servicelayer_url: str, session_configuration: Optional[SessionConfiguration] = None
    ):
        from . import __version__

        auth_url = servicelayer_url.strip("/") + AUTH_PATH
        super().__init__(auth_url, session_configuration)
        self._base_service_layer_url = servicelayer_url
        self._session_configuration.headers[
            "X-Granta-ApplicationName"
        ] = GRANTA_APPLICATION_NAME_HEADER
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
        """Check if the created client can be used to perform a request.

        This method tests both that the API definition can be accessed and that the Granta MI
        version is compatible with this package.

        The first checks ensures that the Server API exists and is functional. The second check
        ensures that the Granta MI server version is compatible with this version of the package.

        A failure at any point raises a ConnectionError.

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
                    "Cannot find the Server API definition in Granta MI Service Layer. Ensure a "
                    "compatible version of Granta MI is available try again."
                ) from e
            else:
                raise ConnectionError(
                    "An unexpected error occurred when trying to connect Server API in Granta MI "
                    "Service Layer. Check the Service Layer logs for more information and try "
                    "again."
                ) from e
        except requests.exceptions.RetryError as e:
            raise ConnectionError(
                "An unexpected error occurred when trying to connect Granta MI Server API. Check "
                "that SSL certificates have been configured for communications between Granta MI "
                "Server and client Granta MI applications."
            ) from e

        try:
            server_version = _get_mi_server_version(client)
        except ApiException as e:
            raise ConnectionError(
                "Cannot check the Granta MI server version. Ensure the Granta MI server version "
                f"is at least {'.'.join([str(e) for e in MINIMUM_GRANTA_MI_VERSION])}."
            ) from e

        # Once there are multiple versions of this package targeting different Granta MI server
        # versions, the error message should direct users towards the PyGranta meta-package for
        # older versions. This is not necessary now though, because there is no support for
        # versions older than 2023 R2.

        if server_version < MINIMUM_GRANTA_MI_VERSION:
            raise ConnectionError(
                f"This package requires a more recent Granta MI version. Detected Granta MI server "
                f"version is {'.'.join([str(e) for e in server_version])}, but this package "
                f"requires at least {'.'.join([str(e) for e in MINIMUM_GRANTA_MI_VERSION])}."
            )
