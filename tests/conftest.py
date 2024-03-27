import datetime
import os
import time

import pytest

from ansys.grantami.jobqueue import Connection, JobQueueApiClient
from common import FOLDER_NAME, clear_job_queue, delete_record, generate_now


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
    if all([admin_username, admin_password]):
        connection = Connection(sl_url).with_credentials(admin_username, admin_password)
    elif not any([admin_username, admin_password]):
        connection = Connection(sl_url).with_autologon()
    else:
        raise ValueError("Specify both or neither of TEST_ADMIN_USER and TEST_ADMIN_PASS.")
    client: JobQueueApiClient = connection.connect()
    yield client


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
    time.sleep(5)
    yield job_queue_api_client
    clear_job_queue(job_queue_api_client)
    delete_record(
        client=job_queue_api_client,
        name=FOLDER_NAME,
    )


@pytest.fixture(scope="function")
def now() -> datetime.datetime:
    return generate_now()


@pytest.fixture(scope="function")
def tomorrow(now) -> datetime.datetime:
    return now + datetime.timedelta(days=1)
