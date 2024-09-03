# Copyright (C) 2024 ANSYS, Inc. and/or its affiliates.
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
import json
from typing import Any, Dict, Optional, Tuple
from unittest.mock import Mock
import uuid

from ansys.grantami.serverapi_openapi import api, models
from ansys.openapi.common import Unset
import pytest

from ansys.grantami.jobqueue import AsyncJob, ImportJob, JobStatus, JobType
from common import generate_now

JOB_ID = str(uuid.uuid4())


@pytest.fixture
def job_model(now, tomorrow):
    mock_job_obj = Mock(spec_set=models.GsaJob())
    mock_job_obj.id = JOB_ID
    mock_job_obj.name = "Mock Job"
    mock_job_obj.description = "Mock description"
    mock_job_obj.status = models.GsaJobStatus.PENDING
    mock_job_obj.type = "ExcelImportJob"
    mock_job_obj.position = 1
    mock_job_obj.submitter_name = "User_1"
    mock_job_obj.submission_date = now
    mock_job_obj.submitter_roles = ["Role1"]
    mock_job_obj.completion_date = None
    mock_job_obj.execution_date = None
    mock_job_obj.scheduled_execution_date = tomorrow
    mock_job_obj.job_specific_outputs = {"JobOutput1": "Good", "JobOutput2": "Bad"}
    mock_job_obj.output_file_names = ["File1, File2"]
    return mock_job_obj


@pytest.fixture
def asyncjob(job_model):
    async_job = AsyncJob(job_obj=job_model, job_queue_api=api.JobQueueApi(Mock()))
    return async_job


class TestUpdateAsyncJob:
    ALL_FIELDS = {
        "name",
        "description",
        "status",
        "scheduled_execution_date",
    }

    def check_patch_call(
        self,
        call_args: Tuple[None, Dict[str, Any]],
        modified_values: Optional[Dict[str, Any]] = None,
    ):
        # No positional args
        assert not call_args[0]

        call_kwargs = call_args[1]

        # id kwarg is always required
        assert call_kwargs["id"] == JOB_ID

        # body kwarg contains the appropriate patch information
        patch_obj = call_kwargs["body"]
        modified_values = {} if not modified_values else modified_values
        unset_values = {arg for arg in type(self).ALL_FIELDS if arg not in modified_values.keys()}
        for arg, val in modified_values.items():
            assert getattr(patch_obj, arg) == val
        for arg in unset_values:
            assert getattr(patch_obj, arg) is Unset

    @staticmethod
    @pytest.fixture
    def mocked_patch_method(asyncjob, job_model, monkeypatch):
        mocked_method = Mock(return_value=job_model)
        monkeypatch.setattr(asyncjob._job_queue_api, "update_job", mocked_method)
        patched_method: Mock = asyncjob._job_queue_api.update_job  # type: ignore
        return patched_method

    def test_update_name(self, mocked_patch_method, asyncjob):
        asyncjob.update_name("Updated name")

        mocked_patch_method.assert_called_once()
        self.check_patch_call(mocked_patch_method.call_args, {"name": "Updated name"})

    def test_update_description(self, mocked_patch_method, asyncjob):
        asyncjob.update_description("Updated description")

        mocked_patch_method.assert_called_once()
        self.check_patch_call(mocked_patch_method.call_args, {"description": "Updated description"})

    def test_update_scheduled_run_date(self, mocked_patch_method, asyncjob):
        try:
            tomorrow = datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=1)
        except AttributeError:
            tomorrow = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=1)

        asyncjob.update_scheduled_execution_date_time(tomorrow)

        mocked_patch_method.assert_called_once()
        self.check_patch_call(mocked_patch_method.call_args, {"scheduled_execution_date": tomorrow})

    @pytest.mark.parametrize(
        "name, value, expected_value, property_name",
        [
            ("id", "New ID", None, None),
            ("name", "New Name", None, None),
            ("description", "New Description", None, None),
            ("description", None, None, None),
            ("description", Unset, None, None),
            ("status", models.GsaJobStatus.FAILED, JobStatus["Failed"], None),
            ("type", "TextImportJob", JobType.TextImportJob, None),
            ("position", 51, None, None),
            ("position", None, None, None),
            ("position", Unset, None, None),
            ("completion_date", generate_now(), None, "completion_date_time"),
            ("completion_date", None, None, "completion_date_time"),
            ("completion_date", Unset, None, "completion_date_time"),
            ("execution_date", generate_now(), None, "execution_date_time"),
            ("execution_date", None, None, "execution_date_time"),
            ("execution_date", Unset, None, "execution_date_time"),
            ("scheduled_execution_date", generate_now(), None, "scheduled_execution_date_time"),
            ("scheduled_execution_date", None, None, "scheduled_execution_date_time"),
            ("scheduled_execution_date", Unset, None, "scheduled_execution_date_time"),
            (
                "job_specific_outputs",
                {"job_specific_outputs": json.dumps({"output": "1", "output_2": "two"})},
                {"job_specific_outputs": {"output": "1", "output_2": "two"}},
                "output_information",
            ),
            ("output_file_names", ["File1", "File 2"], None, "output_file_names"),
            ("output_file_names", [], None, "output_file_names"),
        ],
    )
    def test_job_attribute_update(
        self, asyncjob, job_model, name, value, expected_value, property_name
    ):
        job_model.__setattr__(name, value)
        asyncjob._update_job(job_model)
        if property_name is None:
            updated_value = asyncjob.__getattribute__(name)
        else:
            updated_value = asyncjob.__getattribute__(property_name)
        if value is Unset:
            assert updated_value is None
        else:
            assert updated_value == (expected_value if expected_value else value)

    @pytest.mark.parametrize(
        "name, value, expected_value, property_name",
        [
            ("submitter_name", "New Submitter name", None, "username"),
            ("submission_date", generate_now(), None, "date_time"),
            ("submitter_roles", ["Role1", "Role2"], None, "roles"),
        ],
    )
    def test_submitter_info_update(
        self, asyncjob, job_model, name, value, expected_value, property_name
    ):
        job_model.__setattr__(name, value)
        asyncjob._update_job(job_model)
        updated_value = asyncjob.submitter_information[property_name]
        if value is Unset:
            assert updated_value is None
        else:
            assert updated_value == (expected_value if expected_value else value)

    @pytest.mark.parametrize(
        "name",
        [
            "id",
            "name",
            "status",
            "type",
            "submitter_name",
            "submission_date",
            "submitter_roles",
        ],
    )
    @pytest.mark.parametrize("value", [None, Unset])
    def test_empty_required_fields_raise_exception(self, asyncjob, job_model, name, value):
        job_model.__setattr__(name, value)
        message_id = JOB_ID if name != "id" else value
        with pytest.raises(ValueError, match=f'"{message_id}".*no required field "{name}"'):
            asyncjob._update_job(job_model)


class TestImportJobStatus:
    @pytest.fixture
    def importjob_pending(self, job_model):
        import_job = ImportJob(job_obj=job_model, job_queue_api=api.JobQueueApi(Mock()))
        return import_job

    @pytest.fixture
    def importjob_success(self, job_model):
        job_model.status = models.GsaJobStatus.SUCCEEDED
        job_model.job_specific_outputs = {"summary": json.dumps({"FinishedSuccessfully": True})}
        import_job = ImportJob(job_obj=job_model, job_queue_api=api.JobQueueApi(Mock()))
        return import_job

    @pytest.fixture
    def importjob_failure_success_status(self, job_model):
        job_model.status = models.GsaJobStatus.SUCCEEDED
        job_model.job_specific_outputs = {"summary": json.dumps({"FinishedSuccessfully": False})}
        import_job = ImportJob(job_obj=job_model, job_queue_api=api.JobQueueApi(Mock()))
        return import_job

    @pytest.fixture
    def importjob_failure_failed_status(self, job_model):
        job_model.status = models.GsaJobStatus.FAILED
        job_model.job_specific_outputs = {"summary": "{}"}
        import_job = ImportJob(job_obj=job_model, job_queue_api=api.JobQueueApi(Mock()))
        return import_job

    def test_pending(self, importjob_pending):
        assert importjob_pending.status == JobStatus.Pending

    def test_success(self, importjob_success):
        assert importjob_success.status == JobStatus.Succeeded

    def test_failed_success_status(self, importjob_failure_success_status):
        assert importjob_failure_success_status.status == JobStatus.Failed

    def test_failed_failed_status(self, importjob_failure_failed_status):
        assert importjob_failure_failed_status.status == JobStatus.Failed
