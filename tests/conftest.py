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


@pytest.fixture(scope="function")
def job_queue_api_client(sl_url, admin_username, admin_password):
    """
    Fixture providing a real ApiClient to run integration tests against an instance of Granta MI
    Server API.
    """
    # connection = Connection(sl_url).with_credentials(admin_username, admin_password)
    connection = Connection(sl_url).with_autologon()
    client: JobQueueApiClient = connection.connect()
    clear_job_queue(client)
    delete_record(
        client=client,
        name=FOLDER_NAME,
    )
    yield client
    clear_job_queue(client)
    delete_record(
        client=client,
        name=FOLDER_NAME,
    )


def clear_job_queue(client: JobQueueApiClient):
    try:
        client.delete_jobs(client.jobs)
    except Exception as e:
        warnings.warn(f"Cleanup failed because of {e}\n continuing tests for now")
