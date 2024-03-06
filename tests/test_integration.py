import datetime
import json
import os
import pathlib
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
from common import EXCEL_IMPORT_FOLDER_NAME, TEST_ARTIFACT_DIR, search_for_records_by_name

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def completed_text_import_job(job_queue_api_client: JobQueueApiClient) -> AsyncJob:
    template_path = TEST_ARTIFACT_DIR / "TextImportTestTemplate.xml"
    job_req = TextImportJobRequest(
        name="TextImportTest",
        description="Import test with text",
        data_files=[TEST_ARTIFACT_DIR / "TextDataTest.dat"],
        template_files=[template_path],
    )
    job = job_queue_api_client.create_job_and_wait(job_req)
    return job


@pytest.fixture(scope="module")
def completed_excel_export_job(job_queue_api_client: JobQueueApiClient) -> AsyncJob:
    record_1 = ExportRecord(record_history_identity=123222)
    record_2 = ExportRecord(record_history_identity=123224)
    template_path = TEST_ARTIFACT_DIR / "ExcelExportTest.xlsx"
    job_req = ExcelExportJobRequest(
        name="ExcelImportTest",
        description="Import test 1",
        database_key="MI_Training",
        records=[record_1, record_2],
        template_file=template_path,
    )
    job = job_queue_api_client.create_job_and_wait(job_req)
    return job


@pytest.fixture(scope="module")
def combined_excel_import_file() -> pathlib.Path:
    return TEST_ARTIFACT_DIR / "ExcelImportTest.xlsx"


@pytest.fixture(scope="module")
def excel_export_template() -> pathlib.Path:
    return TEST_ARTIFACT_DIR / "ExcelExportTest.xlsx"


def check_success(output_information, job_type: JobType) -> None:
    if job_type in (JobType.TextImportJob, JobType.ExcelImportJob):
        assert output_information["summary"]["FinishedSuccessfully"]
    elif job_type == JobType.ExcelExportJob:
        assert not output_information["summary"]["Errors"]
    else:
        raise ValueError(f"Unexpected job type {job_type}")


class TestImportJob:
    def test_create_excel_import(self, empty_job_queue_api_client, combined_excel_import_file):
        job_req = ExcelImportJobRequest(
            name="ExcelImportTest",
            description="Import test 1",
            combined_files=[str(combined_excel_import_file)],
        )

        job = empty_job_queue_api_client.create_job_and_wait(job_req)

        assert job.status == JobStatus.Succeeded
        check_success(job.output_information, JobType.ExcelImportJob)

        output_info = job.output_information["summary"]
        assert (
            output_info["NumberOfRecordsCreated"] == 1 or output_info["NumberOfRecordsUpdated"] == 1
        )

    def test_create_text_import(self, empty_job_queue_api_client):
        file_path = TEST_ARTIFACT_DIR / "TextDataTest.dat"
        template_path = pathlib.Path(TEST_ARTIFACT_DIR / "TextImportTestTemplate.xml")
        job_req = TextImportJobRequest(
            name="TextImportTest",
            description="Import test with text",
            data_files=[file_path],
            template_files=[template_path],
        )
        job = empty_job_queue_api_client.create_job_and_wait(job_req)
        assert job.status == JobStatus.Succeeded
        check_success(job.output_information, JobType.TextImportJob)

        output_info = job.output_information["summary"]
        assert (
            output_info["NumberOfRecordsCreated"] == 4 or output_info["NumberOfRecordsUpdated"] == 4
        )

    def test_update_job(self, combined_excel_import_file, empty_job_queue_api_client, tomorrow):
        job_req = ExcelImportJobRequest(
            name="ExcelImportTest",
            description="Import test 1",
            combined_files=[combined_excel_import_file],
        )
        job_req.scheduled_execution_date = tomorrow
        job = empty_job_queue_api_client.create_job(job_req)

        job.update_description("Some random string")
        job.update_name("UpdatedExcelImportTest")

        time.sleep(10)

        assert len(empty_job_queue_api_client.jobs_where(name="UpdatedExcelImportTest")) == 1
        assert empty_job_queue_api_client.jobs[0].description == "Some random string"

    def test_queue_updates_job(self, combined_excel_import_file, empty_job_queue_api_client):
        job_req = ExcelImportJobRequest(
            name="ExcelImportTest",
            description="Import test 1",
            combined_files=[combined_excel_import_file],
        )
        job = empty_job_queue_api_client.create_job(job_req)

        assert job.status == JobStatus.Pending
        time.sleep(10)
        # Fetching jobs updates the jobs list, and hence all linked jobs
        assert len(empty_job_queue_api_client.jobs) == 1

        assert job.status == JobStatus.Succeeded
        check_success(job.output_information, JobType.ExcelImportJob)
        recs_found = search_for_records_by_name(
            client=empty_job_queue_api_client,
            name=EXCEL_IMPORT_FOLDER_NAME,
        )
        assert len(recs_found) == 1

    def test_delete_job(self, combined_excel_import_file, empty_job_queue_api_client, tomorrow):
        with open(TEST_ARTIFACT_DIR / "ExcelImportTest.xlsx", "rb") as f:
            job_req = ExcelImportJobRequest(
                name="ExcelImportTest",
                description="Import test 1",
                combined_files=[combined_excel_import_file],
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


class TestExportJob:
    def test_excel_export_job_single_record(
        self, excel_export_template, empty_job_queue_api_client
    ):
        record = ExportRecord(
            record_history_identity=123222,
        )
        job_req = ExcelExportJobRequest(
            name="ExcelImportTest",
            description="Import test 1",
            database_key="MI_Training",
            records=[record],
            template_file=excel_export_template,
        )
        job = empty_job_queue_api_client.create_job_and_wait(job_req)
        assert job.status == JobStatus.Succeeded
        check_success(job.output_information, JobType.ExcelExportJob)

        output_info = job.output_information["summary"]
        assert output_info["ExportedRecords"] == 1

    def test_excel_export_job_multiple_records_multiple_outputs(
        self, excel_export_template, empty_job_queue_api_client
    ):
        record_1 = ExportRecord(record_history_identity=123222)
        record_2 = ExportRecord(record_history_identity=123224)
        with open(TEST_ARTIFACT_DIR / "ExcelExportTest.xlsx", "rb") as f:
            job_req = ExcelExportJobRequest(
                name="ExcelImportTest",
                description="Import test 1",
                database_key="MI_Training",
                records=[record_1, record_2],
                template_file=excel_export_template,
            )
            job = empty_job_queue_api_client.create_job_and_wait(job_req)
            assert job.status == JobStatus.Succeeded
            check_success(job.output_information, JobType.ExcelExportJob)

            output_info = job.output_information["summary"]
            assert output_info["ExportedRecords"] == 2


class TestFileOutputs:
    def test_import_output_files(self, completed_text_import_job):
        job = completed_text_import_job
        assert job.status == JobStatus.Succeeded
        check_success(job.output_information, JobType.TextImportJob)
        assert len(job.output_file_names) == 2
        summary_filename = next(
            file_name for file_name in job.output_file_names if "summary.json" in file_name
        )
        summary = job.get_file_content(summary_filename)
        parsed_summary = json.loads(summary.decode("utf-8"))
        assert parsed_summary["NumberOfTasks"] == 1
        assert parsed_summary["NumberOfErrors"] == 0

    def test_import_download_files_name(self, completed_text_import_job):
        job = completed_text_import_job
        assert job.status == JobStatus.Succeeded
        assert len(job.output_file_names) == 2
        summary_filepath = next(
            file_name for file_name in job.output_file_names if "summary.json" in file_name
        )
        with tempfile.TemporaryDirectory() as td:
            output_file = os.path.join(td, "file_name.json")
            job.download_file(summary_filepath, output_file)
            assert os.path.exists(output_file)

    def test_import_download_files_path(self, completed_text_import_job):
        job = completed_text_import_job
        assert job.status == JobStatus.Succeeded
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
        assert job.status == JobStatus.Succeeded
        check_success(job.output_information, JobType.ExcelExportJob)
        assert len(job.output_file_names) == 3
        summary_filename = next(
            file_name for file_name in job.output_file_names if "summary.json" in file_name
        )
        summary = job.get_file_content(summary_filename)
        parsed_summary = json.loads(summary.decode("utf-8"))
        assert parsed_summary["ExportedRecords"] == 2
        assert parsed_summary["Errors"] == []


class TestSchedule:
    def test_create_job_with_schedule(
        self, combined_excel_import_file, empty_job_queue_api_client, now
    ):
        with open(TEST_ARTIFACT_DIR / "ExcelImportTest.xlsx", "rb") as f:
            job_req = ExcelImportJobRequest(
                name="ExcelImportTest",
                description="Import test 1",
                combined_files=[combined_excel_import_file],
            )
            job_req.scheduled_execution_date = now + datetime.timedelta(seconds=6)
            job = empty_job_queue_api_client.create_job(job_req)
        time.sleep(2)
        job.update()
        assert job.status == JobStatus.Pending

        time.sleep(15)
        job.update()
        assert job.status == JobStatus.Succeeded
        check_success(job.output_information, JobType.ExcelImportJob)
        recs_found = search_for_records_by_name(
            client=empty_job_queue_api_client,
            name=EXCEL_IMPORT_FOLDER_NAME,
        )
        time.sleep(2)
        assert len(recs_found) == 1

    def test_update_schedule(
        self, combined_excel_import_file, empty_job_queue_api_client, now, tomorrow
    ):
        job_req = ExcelImportJobRequest(
            name="ExcelImportTest",
            description="Import test 1",
            combined_files=[combined_excel_import_file],
        )
        job_req.scheduled_execution_date = tomorrow
        job = empty_job_queue_api_client.create_job(job_req)

        assert job.status == JobStatus.Pending

        job.update_scheduled_execution_date_time(now)
        assert job.scheduled_execution_date_time - now < datetime.timedelta(seconds=5)
        assert job.description == "Import test 1"

        time.sleep(10)
        job.update()

        assert job.status == JobStatus.Succeeded
        check_success(job.output_information, JobType.ExcelImportJob)
        recs_found = search_for_records_by_name(
            client=empty_job_queue_api_client,
            name=EXCEL_IMPORT_FOLDER_NAME,
        )
        assert len(recs_found) == 1
