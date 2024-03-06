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
    "Cannot create Excel import job with both combined and template/data files specified"
)
EXCEL_MISSING_FILES_ERROR_MESSAGE = (
    "Excel import jobs must contain either a 'Combined' file or 'Data' files and a 'Template' file."
)


@pytest.mark.parametrize(
    "combined, data, template, message",
    [
        (
            [EXCEL_IMPORT_COMBINED_FILE],
            [EXCEL_IMPORT_DATA_FILE],
            [EXCEL_IMPORT_TEMPLATE_FILE],
            EXCEL_TOO_MANY_FILES_ERROR_MESSAGE,
        ),
        (
            [EXCEL_IMPORT_COMBINED_FILE],
            None,
            [EXCEL_IMPORT_TEMPLATE_FILE],
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
            [EXCEL_IMPORT_TEMPLATE_FILE],
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
            template_files=template,
            combined_files=combined,
            attachment_files=attachment,
        )


TEXT_ERROR_MESSAGE = "Text import jobs must contain one or more 'Data' files and a 'Template' file"


@pytest.mark.parametrize(
    "data, template",
    [
        (None, None),
        ([TEXT_IMPORT_DATA_FILE], None),
        (None, [TEXT_IMPORT_TEMPLATE_FILE]),
    ],
)
@pytest.mark.parametrize("attachment", [[ATTACHMENT], None])
def test_text_invalid_files_raise_exception(data, template, attachment):
    with pytest.raises(ValueError, match=TEXT_ERROR_MESSAGE):
        TextImportJobRequest(
            name="ExcelImportTest",
            description="Import test 1",
            data_files=data,
            template_files=template,
            attachment_files=attachment,
        )
