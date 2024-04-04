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

import pytest

from ansys.grantami.jobqueue import ExcelImportJobRequest, TextImportJobRequest
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
