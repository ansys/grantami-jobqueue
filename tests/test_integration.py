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
    EXCEL_EXPORT_TEMPLATE_FILE,
    EXCEL_IMPORT_COMBINED_FILE,
    EXCEL_IMPORT_DATA_FILE,
    EXCEL_IMPORT_FOLDER_NAME,
    EXCEL_IMPORT_TEMPLATE_FILE,
    TEST_ARTIFACT_DIR,
    TEXT_IMPORT_DATA_FILE,
    TEXT_IMPORT_TEMPLATE_FILE,
    search_for_records_by_name,
)

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def completed_text_import_job(job_queue_api_client: JobQueueApiClient) -> AsyncJob:
    job_req = TextImportJobRequest(
        name="TextImportTest",
        description="Import test with text",
        data_files=[TEXT_IMPORT_DATA_FILE],
        template_files=[TEXT_IMPORT_TEMPLATE_FILE],
    )
    job = job_queue_api_client.create_job_and_wait(job_req)
    return job


@pytest.fixture(scope="module")
def completed_excel_export_job(job_queue_api_client: JobQueueApiClient) -> AsyncJob:
    record_1 = ExportRecord(record_history_identity=123222)
    record_2 = ExportRecord(record_history_identity=123224)
    job_req = ExcelExportJobRequest(
        name="ExcelImportTest",
        description="Import test 1",
        database_key="MI_Training",
        records=[record_1, record_2],
        template_file=EXCEL_EXPORT_TEMPLATE_FILE,
    )
    job = job_queue_api_client.create_job_and_wait(job_req)
    return job


def check_success(output_information, job_type: JobType) -> None:
    if job_type in (JobType.TextImportJob, JobType.ExcelImportJob):
        assert output_information["summary"]["FinishedSuccessfully"]
    elif job_type == JobType.ExcelExportJob:
        assert not output_information["summary"]["Errors"]
    else:
        raise ValueError(f"Unexpected job type {job_type}")


class TestExcelImportJob:
    def test_create_excel_import_combined_file(self, empty_job_queue_api_client):
        job_req = ExcelImportJobRequest(
            name="ExcelImportTest",
            description="Import test 1",
            combined_files=[str(EXCEL_IMPORT_COMBINED_FILE)],
        )

        job = empty_job_queue_api_client.create_job_and_wait(job_req)

        assert job.status == JobStatus.Succeeded
        check_success(job.output_information, JobType.ExcelImportJob)

        output_info = job.output_information["summary"]
        assert (
            output_info["NumberOfRecordsCreated"] == 1 or output_info["NumberOfRecordsUpdated"] == 1
        )

    def test_create_excel_import_separate_files(self, empty_job_queue_api_client):
        job_req = ExcelImportJobRequest(
            name="ExcelImportTest",
            description="Import test 1",
            template_files=[EXCEL_IMPORT_TEMPLATE_FILE],
            data_files=[EXCEL_IMPORT_DATA_FILE],
        )

        job = empty_job_queue_api_client.create_job_and_wait(job_req)

        assert job.status == JobStatus.Succeeded
        check_success(job.output_information, JobType.ExcelImportJob)

        output_info = job.output_information["summary"]
        assert (
            output_info["NumberOfRecordsCreated"] == 1 or output_info["NumberOfRecordsUpdated"] == 1
        )

    def test_create_text_import(self, empty_job_queue_api_client):
        job_req = TextImportJobRequest(
            name="TextImportTest",
            description="Import test with text",
            data_files=[TEXT_IMPORT_DATA_FILE],
            template_files=[TEXT_IMPORT_TEMPLATE_FILE],
        )
        job = empty_job_queue_api_client.create_job_and_wait(job_req)
        assert job.status == JobStatus.Succeeded
        check_success(job.output_information, JobType.TextImportJob)

        output_info = job.output_information["summary"]
        assert (
            output_info["NumberOfRecordsCreated"] == 4 or output_info["NumberOfRecordsUpdated"] == 4
        )

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

        assert len(empty_job_queue_api_client.jobs_where(name="UpdatedExcelImportTest")) == 1
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

        assert job.status == JobStatus.Succeeded
        check_success(job.output_information, JobType.ExcelImportJob)
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


class TestTextImportJob:
    def test_create_text_import(self, empty_job_queue_api_client):
        job_req = TextImportJobRequest(
            name="TextImportTest",
            description="Import test with text",
            data_files=[TEXT_IMPORT_DATA_FILE],
            template_files=[TEXT_IMPORT_TEMPLATE_FILE],
        )
        job = empty_job_queue_api_client.create_job_and_wait(job_req)
        assert job.status == JobStatus.Succeeded
        check_success(job.output_information, JobType.TextImportJob)

        output_info = job.output_information["summary"]
        assert (
            output_info["NumberOfRecordsCreated"] == 4 or output_info["NumberOfRecordsUpdated"] == 4
        )


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
        assert job.status == JobStatus.Succeeded
        check_success(job.output_information, JobType.ExcelExportJob)

        output_info = job.output_information["summary"]
        assert output_info["ExportedRecords"] == 1

    def test_excel_export_job_multiple_records_multiple_outputs(self, empty_job_queue_api_client):
        record_1 = ExportRecord(record_history_identity=123222)
        record_2 = ExportRecord(record_history_identity=123224)
        with open(TEST_ARTIFACT_DIR / "ExcelExportTest.xlsx", "rb") as f:
            job_req = ExcelExportJobRequest(
                name="ExcelImportTest",
                description="Import test 1",
                database_key="MI_Training",
                records=[record_1, record_2],
                template_file=EXCEL_EXPORT_TEMPLATE_FILE,
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
    def test_create_job_with_schedule(self, empty_job_queue_api_client, now):
        with open(TEST_ARTIFACT_DIR / "ExcelImportTest.xlsx", "rb") as f:
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
        assert job.status == JobStatus.Succeeded
        check_success(job.output_information, JobType.ExcelImportJob)
        recs_found = search_for_records_by_name(
            client=empty_job_queue_api_client,
            name=EXCEL_IMPORT_FOLDER_NAME,
        )
        time.sleep(2)
        assert len(recs_found) == 1

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

        assert job.status == JobStatus.Succeeded
        check_success(job.output_information, JobType.ExcelImportJob)
        recs_found = search_for_records_by_name(
            client=empty_job_queue_api_client,
            name=EXCEL_IMPORT_FOLDER_NAME,
        )
        assert len(recs_found) == 1
