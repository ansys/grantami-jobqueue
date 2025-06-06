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
import pathlib
import time
from typing import List, Tuple, cast

from ansys.grantami.serverapi_openapi.v2025r2 import api, models
from ansys.openapi.common import ApiClient

TEST_ARTIFACT_DIR = pathlib.Path(__file__).parent / "test_artifacts"

DB_KEY = "MI_Training"
TABLE_NAME = "Tensile Test Data"
FOLDER_NAME = "Data Import Test"
EXCEL_IMPORT_FOLDER_NAME = "Excel Import Test"

DATABASE_CACHE_SLEEP = 1
MAX_DATABASE_CACHE_ATTEMPTS = 10

EXCEL_IMPORT_COMBINED_FILE = TEST_ARTIFACT_DIR / "ExcelImportCombinedFile.xlsx"
EXCEL_IMPORT_DATA_FILE = TEST_ARTIFACT_DIR / "ExcelImportDataFile.xlsx"
EXCEL_IMPORT_TEMPLATE_FILE = TEST_ARTIFACT_DIR / "ExcelImportTemplateFile.xlsx"

EXCEL_IMPORT_COMBINED_FILE_WITH_ATTACHMENT = (
    TEST_ARTIFACT_DIR / "ExcelImportCombinedFileWithAttachment.xlsx"
)
EXCEL_IMPORT_DATA_FILE_WITH_ATTACHMENT = (
    TEST_ARTIFACT_DIR / "ExcelImportDataFileWithAttachment.xlsx"
)
ATTACHMENT = TEST_ARTIFACT_DIR / "Attachment.bmp"

EXCEL_EXPORT_TEMPLATE_FILE = TEST_ARTIFACT_DIR / "ExcelExportTemplateFile.xlsx"

TEXT_IMPORT_DATA_FILE = TEST_ARTIFACT_DIR / "TextImportDataFile.dat"
TEXT_IMPORT_TEMPLATE_FILE = TEST_ARTIFACT_DIR / "TextImportTemplateFile.xml"


def generate_now():
    try:
        return datetime.datetime.now(datetime.UTC)
    except AttributeError:
        return datetime.datetime.now(datetime.timezone.utc)


def _get_table_guid(client: ApiClient) -> str:
    schema_tables_api = api.SchemaTablesApi(client)
    all_tables = schema_tables_api.get_tables(
        database_key=DB_KEY,
    )
    table_guid = next(t.guid for t in all_tables.tables if t.name == TABLE_NAME)
    return table_guid


def delete_record(client: ApiClient, name: str) -> None:
    table_guid = _get_table_guid(client=client)

    records = search_for_records_by_name(
        client=client,
        name=name,
    )
    if not records:
        return
    assert len(records) == 1
    record_history_guid, record_guid = records[0]

    record_version_api = api.RecordsRecordVersionsApi(client)
    record_version_api.delete_record_version(
        database_key=DB_KEY,
        table_guid=table_guid,
        record_history_guid=record_history_guid,
        record_version_guid=record_guid,
    )


def search_for_records_by_name(client: ApiClient, name: str) -> List[Tuple[str, str]]:
    database_api = api.DatabaseApi(client)
    counter = 0
    while not database_api.get_search_index_status(database_key=DB_KEY).search_index_up_to_date:
        counter += 1
        if counter == MAX_DATABASE_CACHE_ATTEMPTS:
            raise RuntimeError(
                f"Database {DB_KEY} failed to cache after {MAX_DATABASE_CACHE_ATTEMPTS} attempts."
            )
        time.sleep(DATABASE_CACHE_SLEEP)

    search_criterion = models.GsaBooleanCriterion(
        any=[
            models.GsaRecordPropertyCriterion(
                _property=models.GsaSearchableRecordProperty.RECORDNAME,
                inner_criterion=models.GsaShortTextDatumCriterion(
                    value=name,
                    text_match_behavior=models.GsaTextMatchBehavior.EXACTMATCHCASEINSENSITIVE,
                ),
            ),
            models.GsaRecordPropertyCriterion(
                _property=models.GsaSearchableRecordProperty.TREENAME,
                inner_criterion=models.GsaShortTextDatumCriterion(
                    value=name,
                    text_match_behavior=models.GsaTextMatchBehavior.EXACTMATCHCASEINSENSITIVE,
                ),
            ),
        ]
    )
    request = models.GsaSearchRequest(
        criterion=search_criterion,
    )

    search_api = api.SearchApi(client)
    table_guid = _get_table_guid(client=client)
    response = search_api.database_search_in_table_with_guid(
        database_key=DB_KEY, table_guid=table_guid, body=request
    )
    return [(r.record_history_guid, r.record_guid) for r in response.results]


def get_granta_mi_version(client: ApiClient) -> tuple[int, int] | None:
    schema_api = api.SchemaApi(client)
    version = schema_api.get_version()
    parsed_version = [int(v) for v in version.major_minor_version.split(".")]
    assert len(parsed_version) == 2
    return cast(tuple[int, int], tuple(parsed_version))
