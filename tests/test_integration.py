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
import os
import tempfile
import time

import pytest

from ansys.grantami.jobqueue import (
    AsyncJob,
    ExcelExportJobRequest,
    ExcelImportJobRequest,
    ExportRecord,
    JobQueueApiClient,
    JobStatus,
    JobType,
    TextImportJobRequest,
)
from common import (
    ATTACHMENT,
    EXCEL_EXPORT_TEMPLATE_FILE,
    EXCEL_IMPORT_COMBINED_FILE,
    EXCEL_IMPORT_COMBINED_FILE_WITH_ATTACHMENT,
    EXCEL_IMPORT_DATA_FILE,
    EXCEL_IMPORT_DATA_FILE_WITH_ATTACHMENT,
    EXCEL_IMPORT_FOLDER_NAME,
    EXCEL_IMPORT_TEMPLATE_FILE,
    TEXT_IMPORT_DATA_FILE,
    TEXT_IMPORT_TEMPLATE_FILE,
    search_for_records_by_name,
)

pytestmark = pytest.mark.integration


@pytest.fixture(scope="function")
def completed_excel_combined_import_job(empty_job_queue_api_client: JobQueueApiClient) -> AsyncJob:
    job_req = ExcelImportJobRequest(
        name="ExcelImportTest",
        description="Import test 1",
        combined_files=[str(EXCEL_IMPORT_COMBINED_FILE)],
    )
    job = empty_job_queue_api_client.create_job_and_wait(job_req)
    check_success(job)
    return job


@pytest.fixture(scope="function")
def completed_text_import_job(empty_job_queue_api_client: JobQueueApiClient) -> AsyncJob:
    job_req = TextImportJobRequest(
        name="TextImportTest",
        description="Import test with text",
        data_files=[TEXT_IMPORT_DATA_FILE],
        template_file=TEXT_IMPORT_TEMPLATE_FILE,
    )
    job = empty_job_queue_api_client.create_job_and_wait(job_req)
    check_success(job)
    return job


@pytest.fixture(scope="function")
def completed_excel_export_job(empty_job_queue_api_client: JobQueueApiClient) -> AsyncJob:
    record_1 = ExportRecord(record_history_identity=123222)
    record_2 = ExportRecord(record_history_identity=123224)
    job_req = ExcelExportJobRequest(
        name="ExcelExportTest",
        description="Import test 1",
        database_key="MI_Training",
        records=[record_1, record_2],
        template_file=EXCEL_EXPORT_TEMPLATE_FILE,
    )
    job = empty_job_queue_api_client.create_job_and_wait(job_req)
    check_success(job)
    return job


def check_success(job: AsyncJob) -> None:
    assert job.status == JobStatus.Succeeded

    if job.type in (JobType.TextImportJob, JobType.ExcelImportJob):
        assert job.output_information["summary"]["FinishedSuccessfully"]
        assert job.output_information["summary"]["NumberOfErrors"] == 0
        if job.type == JobType.ExcelExportJob:
            recs_found = search_for_records_by_name(
                client=job._job_queue_api.api_client,  # type: ignore
                name=EXCEL_IMPORT_FOLDER_NAME,
            )
            assert len(recs_found) == 1
    elif job.type == JobType.ExcelExportJob:
        assert not job.output_information["summary"]["Errors"]
    else:
        raise ValueError(f"Unexpected job type {job.type}")


class TestExcelImportJob:
    def test_create_excel_import_combined_file(self, completed_excel_combined_import_job):
        output_info = completed_excel_combined_import_job.output_information["summary"]
        assert output_info["NumberOfRecordsCreated"] == 1
        assert output_info["NumberOfRecordsUpdated"] == 0

    def test_create_excel_import_combined_file_with_attachment(self, empty_job_queue_api_client):
        job_req = ExcelImportJobRequest(
            name="ExcelImportTest combined file with attachment",
            description="Import test 1",
            combined_files=[str(EXCEL_IMPORT_COMBINED_FILE_WITH_ATTACHMENT)],
            attachment_files=[ATTACHMENT],
        )

        job = empty_job_queue_api_client.create_job_and_wait(job_req)

        output_info = job.output_information["summary"]
        assert output_info["NumberOfRecordsCreated"] == 1
        assert output_info["NumberOfRecordsUpdated"] == 0

    def test_create_excel_import_separate_files(self, empty_job_queue_api_client):
        job_req = ExcelImportJobRequest(
            name="ExcelImportTest separate files",
            description="Import test 1",
            template_file=EXCEL_IMPORT_TEMPLATE_FILE,
            data_files=[EXCEL_IMPORT_DATA_FILE],
        )

        job = empty_job_queue_api_client.create_job_and_wait(job_req)

        check_success(job)

        output_info = job.output_information["summary"]
        assert output_info["NumberOfRecordsCreated"] == 1
        assert output_info["NumberOfRecordsUpdated"] == 0

    def test_create_excel_import_separate_files_with_attachment(self, empty_job_queue_api_client):
        job_req = ExcelImportJobRequest(
            name="ExcelImportTest separate files with attachment",
            description="Import test 1",
            template_file=EXCEL_IMPORT_TEMPLATE_FILE,
            data_files=[EXCEL_IMPORT_DATA_FILE_WITH_ATTACHMENT],
            attachment_files=[ATTACHMENT],
        )

        job = empty_job_queue_api_client.create_job_and_wait(job_req)

        check_success(job)

        output_info = job.output_information["summary"]
        assert output_info["NumberOfRecordsCreated"] == 1
        assert output_info["NumberOfRecordsUpdated"] == 0

    def test_update_job(self, empty_job_queue_api_client, tomorrow):
        job_req = ExcelImportJobRequest(
            name="ExcelImportTest",
            description="Import test 1",
            combined_files=[EXCEL_IMPORT_COMBINED_FILE],
        )
        job_req.scheduled_execution_date = tomorrow
        job = empty_job_queue_api_client.create_job(job_req)

        job.update_description("Some random string")
        job.update_name("UpdatedExcelImportTest")

        time.sleep(10)

        assert empty_job_queue_api_client.jobs[0].name == "UpdatedExcelImportTest"
        assert empty_job_queue_api_client.jobs[0].description == "Some random string"

    def test_queue_updates_job(self, empty_job_queue_api_client):
        job_req = ExcelImportJobRequest(
            name="ExcelImportTest",
            description="Import test 1",
            combined_files=[EXCEL_IMPORT_COMBINED_FILE],
        )
        job = empty_job_queue_api_client.create_job(job_req)

        assert job.status == JobStatus.Pending
        time.sleep(10)
        # Fetching jobs updates the jobs list, and hence all linked jobs
        assert len(empty_job_queue_api_client.jobs) == 1

        check_success(job)
        recs_found = search_for_records_by_name(
            client=empty_job_queue_api_client,
            name=EXCEL_IMPORT_FOLDER_NAME,
        )
        assert len(recs_found) == 1

    def test_delete_job(self, empty_job_queue_api_client, tomorrow):
        job_req = ExcelImportJobRequest(
            name="ExcelImportTest",
            description="Import test 1",
            combined_files=[EXCEL_IMPORT_COMBINED_FILE],
        )
        job_req.scheduled_execution_date = tomorrow
        job = empty_job_queue_api_client.create_job(job_req)

        assert job.status == JobStatus.Pending
        assert len(empty_job_queue_api_client.jobs) == 1
        empty_job_queue_api_client.delete_jobs([job])
        assert job.status == JobStatus.Deleted
        assert len(empty_job_queue_api_client.jobs) == 0

        with pytest.raises(ValueError):
            job.update_name("Error")
        with pytest.raises(ValueError):
            job.update_description("Oh no, an error")
        with pytest.raises(ValueError):
            job.update()

    def test_create_excel_import_no_description(self, empty_job_queue_api_client):
        job_req = ExcelImportJobRequest(
            name="ExcelImportTest combined file with attachment",
            description=None,
            combined_files=[str(EXCEL_IMPORT_COMBINED_FILE_WITH_ATTACHMENT)],
            attachment_files=[ATTACHMENT],
        )

        job = empty_job_queue_api_client.create_job_and_wait(job_req)
        assert job.description is None

        output_info = job.output_information["summary"]
        assert output_info["NumberOfRecordsCreated"] == 1
        assert output_info["NumberOfRecordsUpdated"] == 0


class TestTextImportJob:
    def test_create_text_import(self, completed_text_import_job):
        output_info = completed_text_import_job.output_information["summary"]
        assert output_info["NumberOfRecordsCreated"] == 4
        assert output_info["NumberOfRecordsUpdated"] == 0

    def test_create_text_import_no_description(self, empty_job_queue_api_client):
        job_req = TextImportJobRequest(
            name="TextImportTest",
            description=None,
            data_files=[TEXT_IMPORT_DATA_FILE],
            template_file=TEXT_IMPORT_TEMPLATE_FILE,
        )
        job = empty_job_queue_api_client.create_job_and_wait(job_req)
        assert job.description is None

        output_info = job.output_information["summary"]
        assert output_info["NumberOfRecordsCreated"] == 4
        assert output_info["NumberOfRecordsUpdated"] == 0


class TestExportJob:
    def test_excel_export_job_single_record(self, empty_job_queue_api_client):
        record = ExportRecord(
            record_history_identity=123222,
        )
        job_req = ExcelExportJobRequest(
            name="ExcelImportTest",
            description="Import test 1",
            database_key="MI_Training",
            records=[record],
            template_file=EXCEL_EXPORT_TEMPLATE_FILE,
        )
        job = empty_job_queue_api_client.create_job_and_wait(job_req)
        check_success(job)

        output_info = job.output_information["summary"]
        assert output_info["ExportedRecords"] == 1

    def test_excel_export_job_multiple_records_multiple_outputs(self, completed_excel_export_job):
        job = completed_excel_export_job
        check_success(job)

        output_info = job.output_information["summary"]
        assert output_info["ExportedRecords"] == 2

    def test_excel_export_job_no_description(self, empty_job_queue_api_client):
        record = ExportRecord(
            record_history_identity=123222,
        )
        job_req = ExcelExportJobRequest(
            name="ExcelImportTest",
            description=None,
            database_key="MI_Training",
            records=[record],
            template_file=EXCEL_EXPORT_TEMPLATE_FILE,
        )
        job = empty_job_queue_api_client.create_job_and_wait(job_req)
        assert job.description is None
        check_success(job)

        output_info = job.output_information["summary"]
        assert output_info["ExportedRecords"] == 1


class TestFileOutputs:
    def test_excel_import_output_files(self, completed_excel_combined_import_job):
        job = completed_excel_combined_import_job

        assert len(job.output_file_names) == 2
        summary_filename = next(
            file_name for file_name in job.output_file_names if "summary.json" in file_name
        )
        summary = job.get_file_content(summary_filename)
        parsed_summary = json.loads(summary.decode("utf-8"))
        assert parsed_summary["NumberOfTasks"] == 1
        assert parsed_summary["NumberOfErrors"] == 0

    def test_excel_import_download_files_name(self, completed_excel_combined_import_job):
        job = completed_excel_combined_import_job

        assert len(job.output_file_names) == 2
        summary_filepath = next(
            file_name for file_name in job.output_file_names if "summary.json" in file_name
        )
        with tempfile.TemporaryDirectory() as td:
            output_file = os.path.join(td, "file_name.json")
            job.download_file(summary_filepath, output_file)
            assert os.path.exists(output_file)

    def test_excel_import_download_files_path(self, completed_excel_combined_import_job):
        job = completed_excel_combined_import_job

        assert len(job.output_file_names) == 2
        summary_filepath = next(
            file_name for file_name in job.output_file_names if "summary.json" in file_name
        )
        summary_filename = summary_filepath.split("\\")[-1]
        with tempfile.TemporaryDirectory() as td:
            job.download_file(summary_filepath, td)
            output_file = os.path.join(td, summary_filename)
            assert os.path.exists(output_file)

    def test_text_import_output_files(self, completed_text_import_job):
        job = completed_text_import_job

        assert len(job.output_file_names) == 2
        summary_filename = next(
            file_name for file_name in job.output_file_names if "summary.json" in file_name
        )
        summary = job.get_file_content(summary_filename)
        parsed_summary = json.loads(summary.decode("utf-8"))
        assert parsed_summary["NumberOfTasks"] == 1
        assert parsed_summary["NumberOfErrors"] == 0

    def test_text_import_download_files_name(self, completed_text_import_job):
        job = completed_text_import_job

        assert len(job.output_file_names) == 2
        summary_filepath = next(
            file_name for file_name in job.output_file_names if "summary.json" in file_name
        )
        with tempfile.TemporaryDirectory() as td:
            output_file = os.path.join(td, "file_name.json")
            job.download_file(summary_filepath, output_file)
            assert os.path.exists(output_file)

    def test_text_import_download_files_path(self, completed_text_import_job):
        job = completed_text_import_job

        assert len(job.output_file_names) == 2
        summary_filepath = next(
            file_name for file_name in job.output_file_names if "summary.json" in file_name
        )
        summary_filename = summary_filepath.split("\\")[-1]
        with tempfile.TemporaryDirectory() as td:
            job.download_file(summary_filepath, td)
            output_file = os.path.join(td, summary_filename)
            assert os.path.exists(output_file)

    def test_export_output_files(self, completed_excel_export_job):
        job = completed_excel_export_job

        assert len(job.output_file_names) == 3
        summary_filename = next(
            file_name for file_name in job.output_file_names if "summary.json" in file_name
        )
        summary = job.get_file_content(summary_filename)
        parsed_summary = json.loads(summary.decode("utf-8"))
        assert parsed_summary["ExportedRecords"] == 2
        assert parsed_summary["Errors"] == []


class TestSearch:
    def test_search_by_name(
        self, completed_excel_combined_import_job, completed_text_import_job, job_queue_api_client
    ):
        job_name = completed_excel_combined_import_job.name
        assert len(job_queue_api_client.jobs_where(name=job_name)) == 1

    def test_search_by_description(
        self, completed_excel_combined_import_job, completed_text_import_job, job_queue_api_client
    ):
        job_description = completed_text_import_job.description
        assert len(job_queue_api_client.jobs_where(description=job_description)) == 1

    def test_search_by_type(
        self, completed_excel_combined_import_job, completed_text_import_job, job_queue_api_client
    ):
        job_type = completed_text_import_job.type
        assert len(job_queue_api_client.jobs_where(job_type=job_type)) == 1


class TestSchedule:
    def test_create_job_with_schedule(self, empty_job_queue_api_client, now):
        job_req = ExcelImportJobRequest(
            name="ExcelImportTest",
            description="Import test 1",
            combined_files=[EXCEL_IMPORT_COMBINED_FILE],
        )
        job_req.scheduled_execution_date = now + datetime.timedelta(seconds=6)
        job = empty_job_queue_api_client.create_job(job_req)
        time.sleep(2)
        job.update()
        assert job.status == JobStatus.Pending

        time.sleep(15)
        job.update()

        check_success(job)

    def test_update_schedule(self, empty_job_queue_api_client, now, tomorrow):
        job_req = ExcelImportJobRequest(
            name="ExcelImportTest",
            description="Import test 1",
            combined_files=[EXCEL_IMPORT_COMBINED_FILE],
        )
        job_req.scheduled_execution_date = tomorrow
        job = empty_job_queue_api_client.create_job(job_req)

        assert job.status == JobStatus.Pending

        job.update_scheduled_execution_date_time(now)
        assert job.scheduled_execution_date_time - now < datetime.timedelta(seconds=5)
        assert job.description == "Import test 1"

        time.sleep(10)
        job.update()

        check_success(job)
