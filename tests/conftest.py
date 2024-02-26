import datetime
import os
import warnings

import pytest

from ansys.grantami.jobqueue import Connection, JobQueueApiClient
from common import FOLDER_NAME, delete_record


@pytest.fixture(scope="session")
def sl_url():
    return os.getenv("TEST_SL_URL", "http://localhost/mi_servicelayer")


@pytest.fixture(scope="session")
def admin_username():
    return os.getenv("TEST_ADMIN_USER")


@pytest.fixture(scope="session")
def admin_password():
    return os.getenv("TEST_ADMIN_PASS")


@pytest.fixture(scope="session")
def username_read_permissions():
    return os.getenv("TEST_READ_USER")


@pytest.fixture(scope="session")
def password_read_permissions():
    return os.getenv("TEST_READ_PASS")


@pytest.fixture(scope="session")
def job_queue_api_client(sl_url, admin_username, admin_password):
    """
    Fixture providing a real ApiClient to run integration tests against an instance of Granta MI
    Server API.
    """
    connection = Connection(sl_url).with_credentials(admin_username, admin_password)
    client: JobQueueApiClient = connection.connect()
    return client


@pytest.fixture(scope="function")
def empty_job_queue_api_client(job_queue_api_client):
    """
    Fixture providing a real ApiClient to run integration tests against an instance of Granta MI
    Server API.
    """
    clear_job_queue(job_queue_api_client)
    delete_record(
        client=job_queue_api_client,
        name=FOLDER_NAME,
    )
    yield job_queue_api_client
    clear_job_queue(job_queue_api_client)
    delete_record(
        client=job_queue_api_client,
        name=FOLDER_NAME,
    )


@pytest.fixture(scope="function")
def now() -> datetime.datetime:
    try:
        return datetime.datetime.now(datetime.UTC)
    except AttributeError:
        return datetime.datetime.utcnow()


@pytest.fixture(scope="function")
def tomorrow(now) -> datetime.datetime:
    return now + datetime.timedelta(days=1)


def clear_job_queue(client: JobQueueApiClient):
    try:
        client.delete_jobs(client.jobs)
    except Exception as e:
        warnings.warn(f"Cleanup failed because of {e}\n continuing tests for now")
