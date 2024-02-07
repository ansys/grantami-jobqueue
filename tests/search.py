from typing import List

from ansys.grantami.serverapi_openapi import api, models

from ansys.grantami.jobqueue import JobQueueApiClient


def search_for_records_by_name(
    client: JobQueueApiClient, db_key: str, table_name: str, name: str
) -> List[str]:
    schema_tables_api = api.SchemaTablesApi(client)
    search_api = api.SearchApi(client)

    all_tables = schema_tables_api.v1alpha_databases_database_key_tables_get(
        database_key=db_key,
    )
    table_guid = next(t.guid for t in all_tables.tables if t.name == table_name)

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
    response = search_api.v1alpha_databases_database_key_tables_table_guidsearch_post(
        database_key=db_key, table_guid=table_guid, body=request
    )
    return [r.record_guid for r in response.results]
