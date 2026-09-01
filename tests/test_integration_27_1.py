# Copyright (C) 2024 - 2026 Synopsys, Inc. and ANSYS, Inc. All rights reserved.
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

import os
import tempfile

import pytest

from ansys.grantami.jobqueue import (
    AsyncJob,
    ExcelImportDryRunJobRequest,
    ImportJob,
    JobFile,
    JobStatus,
    JobType,
)
from common import (
    EXCEL_IMPORT_COMBINED_FILE,
    EXCEL_IMPORT_DATA_FILE,
    EXCEL_IMPORT_FOLDER_NAME,
    search_for_records_by_name,
)

pytestmark = pytest.mark.integration(mi_versions=[(27, 1)])


def check_success(job: AsyncJob) -> None:
    assert job.status == JobStatus.Succeeded
    assert isinstance(job, ImportJob)
    assert job.output_information["summary"]["FinishedSuccessfully"]
    assert job.output_information["summary"]["NumberOfErrors"] == 0


def get_dry_run_report_file_name(output_file_names: list[str]) -> str:
    return next(
        file_name
        for file_name in output_file_names
        if not file_name.endswith(".log") and "summary.json" not in file_name
    )


class TestExcelImportDryRunJob:
    def test_create_excel_import_dry_run_combined_file(self, empty_job_queue_api_client):
        job_req = ExcelImportDryRunJobRequest(
            name="ExcelImportDryRunTest",
            description="Dry-run import test",
            combined_files=[JobFile(str(EXCEL_IMPORT_COMBINED_FILE), EXCEL_IMPORT_DATA_FILE.name)],
        )
        job = empty_job_queue_api_client.create_job_and_wait(job_req)
        check_success(job)
        assert job.type == JobType.ExcelImportDryRunJob
        assert isinstance(job, ImportJob)

    def test_excel_import_dry_run_output_files(self, empty_job_queue_api_client):
        job_req = ExcelImportDryRunJobRequest(
            name="ExcelImportDryRunTest output files",
            description="Dry-run import test",
            combined_files=[JobFile(str(EXCEL_IMPORT_COMBINED_FILE), EXCEL_IMPORT_DATA_FILE.name)],
        )
        job = empty_job_queue_api_client.create_job_and_wait(job_req)
        check_success(job)

        assert job.output_file_names is not None
        assert len(job.output_file_names) >= 2
        report_file_name = get_dry_run_report_file_name(job.output_file_names)
        assert report_file_name in job.output_file_names

    def test_excel_import_dry_run_download_report(self, empty_job_queue_api_client):
        job_req = ExcelImportDryRunJobRequest(
            name="ExcelImportDryRunTest download report",
            description="Dry-run import test",
            combined_files=[JobFile(str(EXCEL_IMPORT_COMBINED_FILE), EXCEL_IMPORT_DATA_FILE.name)],
        )
        job = empty_job_queue_api_client.create_job_and_wait(job_req)
        check_success(job)

        report_file_name = get_dry_run_report_file_name(job.output_file_names)
        report_content = job.get_file_content(report_file_name)
        assert len(report_content) > 0

        with tempfile.TemporaryDirectory() as td:
            output_file = os.path.join(td, "dry_run_report")
            job.download_file(report_file_name, output_file)
            assert os.path.exists(output_file)

    def test_excel_import_dry_run_no_db_changes(self, empty_job_queue_api_client):
        job_req = ExcelImportDryRunJobRequest(
            name="ExcelImportDryRunTest no db changes",
            description="Dry-run import test",
            combined_files=[JobFile(str(EXCEL_IMPORT_COMBINED_FILE), EXCEL_IMPORT_DATA_FILE.name)],
        )
        job = empty_job_queue_api_client.create_job_and_wait(job_req)
        check_success(job)

        recs_found = search_for_records_by_name(
            client=empty_job_queue_api_client,
            name=EXCEL_IMPORT_FOLDER_NAME,
        )
        assert len(recs_found) == 0
