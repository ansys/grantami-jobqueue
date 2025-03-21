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
from ansys.grantami.jobqueue._connection import MINIMUM_GRANTA_MI_VERSION
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
def job_queue_api_client(sl_url, admin_username, admin_password, mi_version):
    """
    Fixture providing a real ApiClient to run integration tests against an instance of Granta MI
    Server API.

    If client cannot be created because an unsupported Granta MI version is under test, instead yield
    None and skip teardown. Tests that rely on a client being successfully generated should be
    skipped via the 'mi_version' argument to the integration mark.
    """
    if all([admin_username, admin_password]):
        connection = Connection(sl_url).with_credentials(admin_username, admin_password)
    elif not any([admin_username, admin_password]):
        connection = Connection(sl_url).with_autologon()
    else:
        raise ValueError("Specify both or neither of TEST_ADMIN_USER and TEST_ADMIN_PASS.")

    skip_teardown = False
    try:
        client: JobQueueApiClient = connection.connect()
    except ConnectionError as e:
        if mi_version < MINIMUM_GRANTA_MI_VERSION:
            client = None
            skip_teardown = True
        else:
            raise e
    else:
        clear_job_queue(client)
        delete_record(
            client=client,
            name=FOLDER_NAME,
        )
    yield client
    if not skip_teardown:
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


def pytest_addoption(parser):
    parser.addoption("--mi-version", action="store", default=None)


@pytest.fixture(scope="session")
def mi_version(request):
    mi_version: str = request.config.getoption("--mi-version")
    if not mi_version:
        return None
    parsed_version = mi_version.split(".")
    if len(parsed_version) != 2:
        raise ValueError("--mi-version argument must be a MAJOR.MINOR version number")
    version_number = tuple(int(e) for e in parsed_version)
    return version_number


@pytest.fixture(autouse=True)
def process_integration_marks(request, mi_version):
    """Processes the arguments provided to the integration mark.

    If the mark is initialized with the kwarg ``mi_versions``, the value must be of type list[tuple[int, int]], where
    the tuples contain compatible major and minor release versions of Granta MI. If the version is specified for a test
    case and the Granta MI version being tested against is not in the provided list, the test case is skipped.

    Also handles test-specific behavior, for example if a certain Granta MI version and test are incompatible and need
    to be skipped or xfailed.
    """

    # Argument validation
    if not request.node.get_closest_marker("integration"):
        # No integration marker anywhere in the stack
        return
    if mi_version is None:
        # We didn't get an MI version. If integration tests were requested, an MI version must be provided. Raise
        # an exception to fail all tests.
        raise ValueError(
            "No Granta MI Version provided to pytest. Specify Granta MI version with --mi-version MAJOR.MINOR."
        )

    # Process integration mark arguments
    mark: pytest.Mark = request.node.get_closest_marker("integration")
    if not mark.kwargs:
        # Mark not initialized with any keyword arguments
        return
    allowed_versions = mark.kwargs.get("mi_versions")
    if allowed_versions is None:
        return
    if not isinstance(allowed_versions, list):
        raise TypeError("mi_versions argument type must be of type 'list'")
    if mi_version not in allowed_versions:
        formatted_version = ".".join(str(v) for v in mi_version)
        skip_message = f'Test skipped for Granta MI release version "{formatted_version}"'
        pytest.skip(skip_message)
