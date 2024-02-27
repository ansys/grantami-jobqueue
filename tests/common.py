import datetime
import pathlib
import time
from typing import List, Tuple

from ansys.grantami.serverapi_openapi import api, models
from ansys.openapi.common import ApiClient

TEST_ARTIFACT_DIR = pathlib.Path(__file__).parent / "test_artifacts"

DB_KEY = "MI_Training"
TABLE_NAME = "Tensile Test Data"
FOLDER_NAME = "Data Import Test"
EXCEL_IMPORT_FOLDER_NAME = "Excel Import Test"

DATABASE_CACHE_SLEEP = 1
MAX_DATABASE_CACHE_ATTEMPTS = 10


def generate_now():
    try:
        return datetime.datetime.now(datetime.UTC)
    except AttributeError:
        return datetime.datetime.now(datetime.timezone.utc)


def _get_table_guid(client: ApiClient) -> str:
    schema_tables_api = api.SchemaTablesApi(client)
    all_tables = schema_tables_api.v1alpha_databases_database_key_tables_get(
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
    record_version_api.v1alpha_databases_database_key_tables_table_guid_record_histories_record_history_guid_record_versions_record_version_guid_delete(
        database_key=DB_KEY,
        table_guid=table_guid,
        record_history_guid=record_history_guid,
        record_version_guid=record_guid,
    )


def search_for_records_by_name(client: ApiClient, name: str) -> List[Tuple[str, str]]:
    database_api = api.DatabaseApi(client)
    counter = 0
    while not database_api.v1alpha_databases_database_keysearch_index_status_get(
        database_key=DB_KEY
    ).search_index_up_to_date:
        counter += 1
        if counter == MAX_DATABASE_CACHE_ATTEMPTS:
            raise RuntimeError(
                f"Database {DB_KEY} failed to cache after {MAX_DATABASE_CACHE_ATTEMPTS} attempts."
            )
        time.sleep(DATABASE_CACHE_SLEEP)

    search_criterion = models.GrantaServerApiSearchBooleanCriterion(
        any=[
            models.GrantaServerApiSearchRecordPropertyCriterion(
                _property=models.GrantaServerApiSearchSearchableRecordProperty.RECORDNAME,
                inner_criterion=models.GrantaServerApiSearchShortTextDatumCriterion(
                    value=name,
                    text_match_behaviour=models.GrantaServerApiSearchTextMatchBehaviour.EXACTMATCHCASEINSENSITIVE,
                ),
            ),
            models.GrantaServerApiSearchRecordPropertyCriterion(
                _property=models.GrantaServerApiSearchSearchableRecordProperty.TREENAME,
                inner_criterion=models.GrantaServerApiSearchShortTextDatumCriterion(
                    value=name,
                    text_match_behaviour=models.GrantaServerApiSearchTextMatchBehaviour.EXACTMATCHCASEINSENSITIVE,
                ),
            ),
        ]
    )
    request = models.GrantaServerApiSearchSearchRequest(
        criterion=search_criterion,
    )

    search_api = api.SearchApi(client)
    table_guid = _get_table_guid(client=client)
    response = search_api.v1alpha_databases_database_key_tables_table_guidsearch_post(
        database_key=DB_KEY, table_guid=table_guid, body=request
    )
    return [(r.record_history_guid, r.record_guid) for r in response.results]
