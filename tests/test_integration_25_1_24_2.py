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
import json
import os
from pathlib import Path
import shutil
import tempfile
import time

from ansys.openapi.common import ApiException
import pytest

from ansys.grantami.jobqueue import (
    AsyncJob,
    ExcelExportJobRequest,
    ExcelImportJobRequest,
    ExportJob,
    ExportRecord,
    ImportJob,
    JobFile,
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

pytestmark = pytest.mark.integration(mi_versions=[(24, 2), (25, 1)])


@pytest.fixture(scope="function")
def completed_excel_combined_import_job(empty_job_queue_api_client: JobQueueApiClient) -> AsyncJob:
    job_req = ExcelImportJobRequest(
        name="ExcelImportTest",
        description="Import test 1",
        combined_files=[JobFile(str(EXCEL_IMPORT_COMBINED_FILE), EXCEL_IMPORT_DATA_FILE.name)],
    )
    job = empty_job_queue_api_client.create_job_and_wait(job_req)
    check_success(job)
    return job


@pytest.fixture(scope="function")
def completed_text_import_job(empty_job_queue_api_client: JobQueueApiClient) -> AsyncJob:
    job_req = TextImportJobRequest(
        name="TextImportTest",
        description="Import test with text",
        data_files=[JobFile(TEXT_IMPORT_DATA_FILE, TEXT_IMPORT_DATA_FILE.name)],
        template_file=JobFile(TEXT_IMPORT_TEMPLATE_FILE, TEXT_IMPORT_TEMPLATE_FILE.name),
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
        assert isinstance(job, ImportJob)
        assert job.output_information["summary"]["FinishedSuccessfully"]
        assert job.output_information["summary"]["NumberOfErrors"] == 0
        if job.type == JobType.ExcelExportJob:
            recs_found = search_for_records_by_name(
                client=job._job_queue_api.api_client,  # type: ignore
                name=EXCEL_IMPORT_FOLDER_NAME,
            )
            assert len(recs_found) == 1
    elif job.type == JobType.ExcelExportJob:
        assert isinstance(job, ExportJob)
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
            combined_files=[
                JobFile(
                    str(EXCEL_IMPORT_COMBINED_FILE_WITH_ATTACHMENT),
                    EXCEL_IMPORT_COMBINED_FILE_WITH_ATTACHMENT.name,
                )
            ],
            attachment_files=[JobFile(ATTACHMENT, ATTACHMENT.name)],
        )

        job = empty_job_queue_api_client.create_job_and_wait(job_req)

        output_info = job.output_information["summary"]
        assert output_info["NumberOfRecordsCreated"] == 1
        assert output_info["NumberOfRecordsUpdated"] == 0

    def test_create_excel_import_separate_files(self, empty_job_queue_api_client):
        job_req = ExcelImportJobRequest(
            name="ExcelImportTest separate files",
            description="Import test 1",
            template_file=JobFile(EXCEL_IMPORT_TEMPLATE_FILE, EXCEL_IMPORT_TEMPLATE_FILE.name),
            data_files=[JobFile(EXCEL_IMPORT_DATA_FILE, EXCEL_IMPORT_DATA_FILE.name)],
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
            template_file=JobFile(EXCEL_IMPORT_TEMPLATE_FILE, EXCEL_IMPORT_TEMPLATE_FILE.name),
            data_files=[
                JobFile(
                    EXCEL_IMPORT_DATA_FILE_WITH_ATTACHMENT,
                    EXCEL_IMPORT_DATA_FILE_WITH_ATTACHMENT.name,
                )
            ],
            attachment_files=[JobFile(ATTACHMENT, ATTACHMENT.name)],
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
            combined_files=[JobFile(EXCEL_IMPORT_COMBINED_FILE, EXCEL_IMPORT_COMBINED_FILE.name)],
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
            combined_files=[JobFile(EXCEL_IMPORT_COMBINED_FILE, EXCEL_IMPORT_COMBINED_FILE.name)],
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
            combined_files=[JobFile(EXCEL_IMPORT_COMBINED_FILE, EXCEL_IMPORT_COMBINED_FILE.name)],
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
            combined_files=[
                JobFile(str(EXCEL_IMPORT_COMBINED_FILE_WITH_ATTACHMENT), "datafile.xlsx")
            ],
            attachment_files=[JobFile(ATTACHMENT, ATTACHMENT.name)],
        )

        job = empty_job_queue_api_client.create_job_and_wait(job_req)
        assert job.description is None

        output_info = job.output_information["summary"]
        assert output_info["NumberOfRecordsCreated"] == 1
        assert output_info["NumberOfRecordsUpdated"] == 0

    def test_invalid_excel_import(self, empty_job_queue_api_client):
        job_req = ExcelImportJobRequest(
            name="Invalid combined file",
            description="Invalid combined file",
            combined_files=[JobFile(__file__, "test_integration_25_1_24_2.py")],
        )

        job = empty_job_queue_api_client.create_job_and_wait(job_req)
        assert job.status == JobStatus.Failed

        output_info = job.output_information["summary"]
        assert output_info["NumberOfRecordsCreated"] == 0
        assert output_info["NumberOfRecordsUpdated"] == 0
        assert output_info["FinishedSuccessfully"] is False

    def test_delete_failed_job(self, empty_job_queue_api_client):
        job_req = ExcelImportJobRequest(
            name="Invalid combined file",
            description="Invalid combined file",
            combined_files=[JobFile(__file__, "test_integration_25_1_24_2.py")],
        )

        job = empty_job_queue_api_client.create_job_and_wait(job_req)
        assert job.status == JobStatus.Failed

        empty_job_queue_api_client.delete_jobs([job])
        assert job.status == JobStatus.Deleted


class TestTextImportJob:
    def test_create_text_import(self, completed_text_import_job):
        output_info = completed_text_import_job.output_information["summary"]
        assert output_info["NumberOfRecordsCreated"] == 4
        assert output_info["NumberOfRecordsUpdated"] == 0

    def test_create_text_import_no_description(self, empty_job_queue_api_client):
        job_req = TextImportJobRequest(
            name="TextImportTest",
            description=None,
            data_files=[JobFile(TEXT_IMPORT_DATA_FILE, TEXT_IMPORT_DATA_FILE.name)],
            template_file=JobFile(TEXT_IMPORT_TEMPLATE_FILE, TEXT_IMPORT_TEMPLATE_FILE.name),
        )
        job = empty_job_queue_api_client.create_job_and_wait(job_req)
        assert job.description is None

        output_info = job.output_information["summary"]
        assert output_info["NumberOfRecordsCreated"] == 4
        assert output_info["NumberOfRecordsUpdated"] == 0

    def test_invalid_text_import(self, empty_job_queue_api_client):
        job_req = TextImportJobRequest(
            name="Invalid template file",
            description="Invalid template file",
            template_file=JobFile(__file__, "file_1.py"),
            data_files=[JobFile(__file__, "file_2.py")],
        )

        job = empty_job_queue_api_client.create_job_and_wait(job_req)
        assert job.status == JobStatus.Failed

        output_info = job.output_information["summary"]
        assert output_info["NumberOfRecordsCreated"] == 0
        assert output_info["NumberOfRecordsUpdated"] == 0
        assert output_info["FinishedSuccessfully"] is False


class TestPaths:
    template_filename = "template.xml"
    datafile_filename = "data.dat"
    attachment_filename = "picture.bmp"

    @pytest.fixture(scope="class")
    def directory(self, tmp_path_factory):
        yield tmp_path_factory.mktemp("directory")

    @pytest.fixture(scope="class")
    def template_path_absolute(self, directory):
        template_path = Path(directory, self.template_filename)
        shutil.copy(TEXT_IMPORT_TEMPLATE_FILE, template_path)
        yield template_path.absolute()

    @pytest.fixture(scope="class")
    def datafile_path_absolute(self, directory):
        datafile_path = Path(directory, self.datafile_filename)
        shutil.copy(TEXT_IMPORT_DATA_FILE, datafile_path)
        yield datafile_path.absolute()

    @pytest.fixture(scope="class")
    def attachment_path_absolute(self, directory):
        attachment_path = Path(directory, self.attachment_filename)
        shutil.copy(ATTACHMENT, attachment_path)
        yield attachment_path.absolute()

    @pytest.fixture(scope="class")
    def populated_directory(
        self, directory, template_path_absolute, datafile_path_absolute, attachment_path_absolute
    ):
        yield directory

    def make_request(self, queue, template, datafile, attachment) -> AsyncJob:
        job_request = TextImportJobRequest(
            name="TextImportTest",
            description="TextImportTestDescription",
            template_file=template,
            data_files=[datafile],
            attachment_files=[attachment],
        )
        return queue.create_job(job_request)

    def test_using_filenames(self, empty_job_queue_api_client, populated_directory, monkeypatch):
        monkeypatch.chdir(populated_directory)
        job = self.make_request(
            queue=empty_job_queue_api_client,
            template=self.template_filename,
            datafile=self.datafile_filename,
            attachment=self.attachment_filename,
        )
        assert job.status in [JobStatus.Pending, JobStatus.Running, JobStatus.Succeeded]

    def test_using_relative_paths(
        self, empty_job_queue_api_client, populated_directory, monkeypatch
    ):
        cwd = populated_directory.parent
        monkeypatch.chdir(cwd)
        job = self.make_request(
            queue=empty_job_queue_api_client,
            template=Path(populated_directory.name, self.template_filename),
            datafile=Path(populated_directory.name, self.datafile_filename),
            attachment=Path(populated_directory.name, self.attachment_filename),
        )
        assert job.status in [JobStatus.Pending, JobStatus.Running, JobStatus.Succeeded]

    @pytest.mark.integration(mi_versions=[(25, 1)])
    @pytest.mark.parametrize("argument_name", ["template", "datafile", "attachment"])
    def test_any_absolute_path_raises_exception(
        self, empty_job_queue_api_client, populated_directory, monkeypatch, argument_name
    ):
        monkeypatch.chdir(populated_directory)
        kwargs = {
            "template": self.template_filename,
            "datafile": self.datafile_filename,
            "attachment": self.attachment_filename,
        }
        kwargs[argument_name] = Path(kwargs[argument_name]).absolute()
        with pytest.raises(ApiException, match="not safe relative paths"):
            job = self.make_request(
                queue=empty_job_queue_api_client,
                **kwargs,
            )

    def test_wrapped_absolute_path_work(
        self,
        empty_job_queue_api_client,
        populated_directory,
        monkeypatch,
        template_path_absolute,
        datafile_path_absolute,
        attachment_path_absolute,
    ):
        monkeypatch.chdir(populated_directory)
        job = self.make_request(
            queue=empty_job_queue_api_client,
            template=JobFile(template_path_absolute, Path(self.template_filename)),
            datafile=JobFile(datafile_path_absolute, Path(self.datafile_filename)),
            attachment=JobFile(attachment_path_absolute, Path(self.attachment_filename)),
        )
        assert job.status in [JobStatus.Pending, JobStatus.Running, JobStatus.Succeeded]


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
            combined_files=[JobFile(EXCEL_IMPORT_COMBINED_FILE, EXCEL_IMPORT_COMBINED_FILE.name)],
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
            combined_files=[JobFile(EXCEL_IMPORT_COMBINED_FILE, EXCEL_IMPORT_COMBINED_FILE.name)],
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
