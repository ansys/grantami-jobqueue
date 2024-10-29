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
from contextlib import nullcontext as does_not_raise
from pathlib import Path
import sys

import pytest

from ansys.grantami.jobqueue import ExcelImportJobRequest, JobFile, TextImportJobRequest
from common import (
    ATTACHMENT,
    EXCEL_IMPORT_COMBINED_FILE,
    EXCEL_IMPORT_DATA_FILE,
    EXCEL_IMPORT_TEMPLATE_FILE,
    TEXT_IMPORT_DATA_FILE,
    TEXT_IMPORT_TEMPLATE_FILE,
)

EXCEL_TOO_MANY_FILES_ERROR_MESSAGE = (
    "Cannot create Excel import job with both combined and template/data files specified."
)
EXCEL_MISSING_FILES_ERROR_MESSAGE = (
    "Excel import jobs must contain either a combined file or both a template file and data files."
)


@pytest.mark.parametrize(
    "combined, data, template, message",
    [
        (
            [EXCEL_IMPORT_COMBINED_FILE],
            [EXCEL_IMPORT_DATA_FILE],
            EXCEL_IMPORT_TEMPLATE_FILE,
            EXCEL_TOO_MANY_FILES_ERROR_MESSAGE,
        ),
        (
            [EXCEL_IMPORT_COMBINED_FILE],
            None,
            EXCEL_IMPORT_TEMPLATE_FILE,
            EXCEL_TOO_MANY_FILES_ERROR_MESSAGE,
        ),
        (
            [EXCEL_IMPORT_COMBINED_FILE],
            [EXCEL_IMPORT_DATA_FILE],
            None,
            EXCEL_TOO_MANY_FILES_ERROR_MESSAGE,
        ),
        (
            None,
            None,
            None,
            EXCEL_MISSING_FILES_ERROR_MESSAGE,
        ),
        (
            None,
            [EXCEL_IMPORT_DATA_FILE],
            None,
            EXCEL_MISSING_FILES_ERROR_MESSAGE,
        ),
        (
            None,
            None,
            EXCEL_IMPORT_TEMPLATE_FILE,
            EXCEL_MISSING_FILES_ERROR_MESSAGE,
        ),
    ],
)
@pytest.mark.parametrize("attachment", [[ATTACHMENT], None])
def test_excel_invalid_files_raise_exception(combined, data, template, attachment, message):
    with pytest.raises(ValueError, match=message):
        ExcelImportJobRequest(
            name="ExcelImportTest",
            description="Import test 1",
            data_files=data,
            template_file=template,
            combined_files=combined,
            attachment_files=attachment,
        )


@pytest.mark.parametrize(
    "data, template",
    [
        (None, None),
        ([TEXT_IMPORT_DATA_FILE], None),
        (None, TEXT_IMPORT_TEMPLATE_FILE),
    ],
)
@pytest.mark.parametrize("attachment", [[ATTACHMENT], None])
def test_text_invalid_files_raise_exception(data, template, attachment):
    with pytest.raises(
        ValueError,
        match="Text import jobs must contain one or more data files and a template file.",
    ):
        TextImportJobRequest(
            name="ExcelImportTest",
            description="Import test 1",
            data_files=data,
            template_file=template,
            attachment_files=attachment,
        )


@pytest.mark.parametrize(
    ["template_file", "data_files", "combined_files", "attachment_files"],
    [
        pytest.param(
            None,
            [JobFile("", "data.xslx"), JobFile("", "data.xslx")],
            None,
            None,
            id="clash-between-virtual-paths",
        ),
        pytest.param(
            None,
            ["data_1.xslx", JobFile("data_2.xlsx", "data_1.xslx")],
            None,
            None,
            id="clash-between-virtual-path-and-local-path",
        ),
        pytest.param(
            "template.xslx",
            [JobFile("data_2.xlsx", "template.xslx")],
            None,
            None,
            id="clash-between-different-file-types-0-data",
        ),
        pytest.param(
            "files/template.xslx",
            [JobFile("data_2.xlsx", Path("files", "template.xslx"))],
            None,
            None,
            id="clash-between-different-file-types-with-paths",
        ),
        pytest.param(
            None,
            None,
            ["combined_1.xslx", JobFile("combined_2.xlsx", "combined_1.xslx")],
            None,
            id="combined-files",
        ),
        pytest.param(
            None,
            None,
            None,
            ["attachment_1.png", JobFile("attachment_2.png", "attachment_1.png")],
            id="attachments-files",
        ),
        pytest.param(
            None,
            None,
            None,
            [
                "attachment_1.png",
                "attachment_1.png",
            ],
            id="attachments-files-duplicated-string-paths",
        ),
    ],
)
def test_identical_paths_raise_exception(
    template_file, data_files, combined_files, attachment_files
):
    with pytest.raises(ValueError, match="are not unique"):
        job = ExcelImportJobRequest(
            name="TestIdenticalPaths",
            description=None,
            template_file=template_file,
            data_files=data_files,
            combined_files=combined_files,
            attachment_files=attachment_files,
        )


path_error = pytest.raises(
    ValueError, match="Virtual path must be a relative path within the current directory."
)


@pytest.mark.parametrize(
    ["virtual_path", "expectation"],
    [
        (Path("./some/folder/data.txt"), does_not_raise()),
        (Path("data.txt"), does_not_raise()),
        (Path("../data.txt"), path_error),
        pytest.param(
            Path("C:/some/folder/data.txt"),
            path_error,
            marks=pytest.mark.skipif(not sys.platform.startswith("win"), reason="Windows only"),
        ),
        pytest.param(
            Path("//server/share/data.txt"),
            path_error,
            marks=pytest.mark.skipif(not sys.platform.startswith("win"), reason="Windows only"),
        ),
        pytest.param(
            Path("\\\\remote\\c$"),
            path_error,
            marks=pytest.mark.skipif(not sys.platform.startswith("win"), reason="Windows only"),
        ),
        pytest.param(
            Path("/etc/file.txt"),
            path_error,
            marks=pytest.mark.skipif(sys.platform.startswith("win"), reason="Linux only"),
        ),
        pytest.param(
            Path("~/folder/file.txt"),
            path_error,
            marks=pytest.mark.skipif(sys.platform.startswith("win"), reason="Linux only"),
        ),
    ],
)
def test_virtual_path_validation(virtual_path, expectation):
    with expectation:
        JobFile._validate_virtual_path(virtual_path)
