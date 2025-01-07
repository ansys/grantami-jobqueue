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

import datetime
import os
import warnings

import pytest

from ansys.grantami.jobqueue import Connection, JobQueueApiClient
from common import FOLDER_NAME, delete_record, generate_now


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
    return generate_now()


@pytest.fixture(scope="function")
def tomorrow(now) -> datetime.datetime:
    return now + datetime.timedelta(days=1)


def clear_job_queue(client: JobQueueApiClient):
    try:
        client.delete_jobs(client.jobs)
    except Exception as e:
        warnings.warn(f"Cleanup failed because of {e}\n continuing tests for now")
