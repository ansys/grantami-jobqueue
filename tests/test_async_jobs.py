import datetime
import json
import os
import pathlib
import tempfile
import time

import pytest

from ansys.grantami.jobqueue import (
    ExcelImportJobRequest,
    JobQueueApiClient,
    JobStatus,
    TextImportJobRequest,
)
from search import search_for_records_by_name

TEST_ARTIFACT_DIR = pathlib.Path("__file__").parent / "test_artifacts"


def import_text(client: JobQueueApiClient):
    template_path = TEST_ARTIFACT_DIR / "TextImportTestTemplate.xml"
    job_req = TextImportJobRequest(
        name="TextImportTest",
        description="Import test with text",
        data_files=[TEST_ARTIFACT_DIR / "TextDataTest.dat"],
        template_files=[template_path],
    )
    job = client.create_import_job_and_wait(job_req)
    return job


def check_success(output_information) -> None:
    assert output_information["summary"]["FinishedSuccessfully"]


def test_create_excel_import(job_queue_api_client):
    file_path = TEST_ARTIFACT_DIR / "ExcelImportTest.xlsx"
    job_req = ExcelImportJobRequest(
        name="ExcelImportTest", description="Import test 1", combined_files=[str(file_path)]
    )

    job = job_queue_api_client.create_import_job_and_wait(job_req)

    assert job.status == JobStatus.Succeeded
    check_success(job.output_information)

    output_info = job.output_information["summary"]
    assert output_info["NumberOfRecordsCreated"] == 1 or output_info["NumberOfRecordsUpdated"] == 1


def test_no_data_combined():
    with pytest.raises(ValueError) as excinfo:
        _ = ExcelImportJobRequest(name="ExcelImportTest", description="Import test no data")
    assert "Excel import jobs must contain either" in str(excinfo.value)


def test_both_combined_and_template():
    with pytest.raises(ValueError) as excinfo:
        _ = ExcelImportJobRequest(
            name="ExcelImportTest",
            description="Import test with too much data",
            combined_files=[TEST_ARTIFACT_DIR / "TextDataTest.dat"],
            template_files=[TEST_ARTIFACT_DIR / "TextDataTest.dat"],
        )
    assert "Cannot create Excel import job with both" in str(excinfo.value)


def test_create_text_import(job_queue_api_client):
    with open(TEST_ARTIFACT_DIR / "TextDataTest.dat", "rb") as fd:
        template_path = pathlib.Path(TEST_ARTIFACT_DIR / "TextImportTestTemplate.xml")
        job_req = TextImportJobRequest(
            name="TextImportTest",
            description="Import test with text",
            data_files=[fd],
            template_files=[template_path],
        )
        job = job_queue_api_client.create_import_job_and_wait(job_req)
    assert job.status == JobStatus.Succeeded
    check_success(job.output_information)

    output_info = job.output_information["summary"]
    assert output_info["NumberOfRecordsCreated"] == 4 or output_info["NumberOfRecordsUpdated"] == 4


def test_output_files(job_queue_api_client):
    job = import_text(job_queue_api_client)
    assert job.status == JobStatus.Succeeded
    check_success(job.output_information)
    assert len(job.output_file_names) == 2
    summary_filename = next(
        file_name for file_name in job.output_file_names if "summary.json" in file_name
    )
    summary = job.get_file_content(summary_filename)
    parsed_summary = json.loads(summary.decode("utf-8"))
    assert parsed_summary["NumberOfTasks"] == 1
    assert parsed_summary["NumberOfErrors"] == 0


def test_download_files_name(job_queue_api_client):
    job = import_text(job_queue_api_client)
    assert job.status == JobStatus.Succeeded
    assert len(job.output_file_names) == 2
    summary_filepath = next(
        file_name for file_name in job.output_file_names if "summary.json" in file_name
    )
    with tempfile.TemporaryDirectory() as td:
        output_file = os.path.join(td, "file_name.json")
        job.download_file(summary_filepath, output_file)
        assert os.path.exists(output_file)


def test_download_files_path(job_queue_api_client):
    job = import_text(job_queue_api_client)
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


def test_create_job_with_schedule(job_queue_api_client):
    with open(TEST_ARTIFACT_DIR / "ExcelImportTest.xlsx", "rb") as f:
        job_req = ExcelImportJobRequest(
            name="ExcelImportTest", description="Import test 1", combined_files=[f]
        )
        job_req.scheduled_execution_date = datetime.datetime.now(datetime.UTC) + datetime.timedelta(
            seconds=6
        )
        job = job_queue_api_client.create_import_job(job_req)
    time.sleep(2)
    job.update()
    assert job.status == JobStatus.Pending

    time.sleep(15)
    job.update()
    assert job.status == JobStatus.Succeeded
    check_success(job.output_information)
    recs_found = search_for_records_by_name(
        client=job_queue_api_client,
        db_key="DATA_IMPORT_TEST",
        table_name="Data Import Non Versioned",
        name="Excel Import Test",
    )
    time.sleep(2)
    assert len(recs_found) == 1


def test_update_schedule(job_queue_api_client):
    with open(TEST_ARTIFACT_DIR / "ExcelImportTest.xlsx", "rb") as f:
        job_req = ExcelImportJobRequest(
            name="ExcelImportTest", description="Import test 1", combined_files=[f]
        )
        job_req.scheduled_execution_date = datetime.datetime.now(datetime.UTC) + datetime.timedelta(
            days=1
        )
        job = job_queue_api_client.create_import_job(job_req)

    assert job.status == JobStatus.Pending

    now = datetime.datetime.now(datetime.UTC).replace(microsecond=0)
    job.update_scheduled_execution_date_time(now)
    assert job.scheduled_execution_date_time - now < datetime.timedelta(seconds=5)

    time.sleep(10)
    job.update()

    assert job.status == JobStatus.Succeeded
    check_success(job.output_information)
    recs_found = search_for_records_by_name(
        client=job_queue_api_client,
        db_key="DATA_IMPORT_TEST",
        table_name="Data Import Non Versioned",
        name="Excel Import Test",
    )
    assert len(recs_found) == 1


def test_update_job(job_queue_api_client):
    with open(TEST_ARTIFACT_DIR / "ExcelImportTest.xlsx", "rb") as f:
        job_req = ExcelImportJobRequest(
            name="ExcelImportTest", description="Import test 1", combined_files=[f]
        )
        job_req.scheduled_execution_date = datetime.datetime.now(datetime.UTC) + datetime.timedelta(
            days=1
        )
        job = job_queue_api_client.create_import_job(job_req)

    job.update_description("Updated description")
    job.update_name("UpdatedExcelImportTest")

    time.sleep(10)

    assert len(job_queue_api_client.jobs_where(name="UpdatedExcelImportTest")) == 1
    assert len(job_queue_api_client.jobs_where(description="Updated")) == 1


def test_queue_updates_job(job_queue_api_client):
    with open(TEST_ARTIFACT_DIR / "ExcelImportTest.xlsx", "rb") as f:
        job_req = ExcelImportJobRequest(
            name="ExcelImportTest", description="Import test 1", combined_files=[f]
        )
        job = job_queue_api_client.create_import_job(job_req)

    assert job.status == JobStatus.Pending
    time.sleep(10)
    # Fetching jobs updates the jobs list, and hence all linked jobs
    assert len(job_queue_api_client.jobs) == 1

    assert job.status == JobStatus.Succeeded
    check_success(job.output_information)
    recs_found = search_for_records_by_name(
        client=job_queue_api_client,
        db_key="DATA_IMPORT_TEST",
        table_name="Data Import Non Versioned",
        name="Excel Import Test",
    )
    assert len(recs_found) == 1


def test_delete_job(job_queue_api_client):
    with open(TEST_ARTIFACT_DIR / "ExcelImportTest.xlsx", "rb") as f:
        job_req = ExcelImportJobRequest(
            name="ExcelImportTest", description="Import test 1", combined_files=[f]
        )
        job_req.scheduled_execution_date = datetime.datetime.now(datetime.UTC) + datetime.timedelta(
            days=1
        )
        job = job_queue_api_client.create_import_job(job_req)

    assert job.status == JobStatus.Pending
    assert len(job_queue_api_client.jobs) == 1
    job_queue_api_client.delete_jobs([job])
    assert job.status == JobStatus.Deleted
    assert len(job_queue_api_client.jobs) == 0

    with pytest.raises(ValueError):
        job.update_name("Error")
    with pytest.raises(ValueError):
        job.update_description("Oh no, an error")
    with pytest.raises(ValueError):
        job.update()
