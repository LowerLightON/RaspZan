from fastapi.testclient import TestClient

from app.main import app


def _openapi_schema() -> dict:
    return TestClient(app).get("/openapi.json").json()


def _responses(schema: dict, path: str, method: str) -> dict:
    return schema["paths"][path][method]["responses"]


def _query_parameter_names(schema: dict, path: str, method: str) -> set[str]:
    operation = schema["paths"][path][method]
    return {
        parameter["name"]
        for parameter in operation["parameters"]
        if parameter["in"] == "query"
    }


def test_openapi_contains_api_error_response_schema() -> None:
    schema = _openapi_schema()

    assert "ApiErrorResponse" in schema["components"]["schemas"]


def test_schedule_write_endpoints_document_error_responses() -> None:
    schema = _openapi_schema()
    endpoints = [
        ("/schedule/entries", "post"),
        ("/schedule/entries/{entry_id}", "put"),
        ("/schedule/entries/{entry_id}/cancel", "post"),
        ("/schedule/entries/{entry_id}/replace", "post"),
    ]

    for path, method in endpoints:
        responses = _responses(schema, path, method)

        assert {"401", "403", "422"}.issubset(responses)
        for status_code in ("401", "403", "422"):
            schema_ref = responses[status_code]["content"]["application/json"][
                "schema"
            ]["$ref"]
            assert schema_ref == "#/components/schemas/ApiErrorResponse"


def test_schedule_history_endpoint_documents_error_responses() -> None:
    schema = _openapi_schema()
    responses = _responses(schema, "/schedule/entries/{entry_id}/history", "get")

    assert {"404", "422"}.issubset(responses)
    for status_code in ("404", "422"):
        schema_ref = responses[status_code]["content"]["application/json"][
            "schema"
        ]["$ref"]
        assert schema_ref == "#/components/schemas/ApiErrorResponse"


def test_schedule_read_endpoints_document_validation_errors() -> None:
    schema = _openapi_schema()
    endpoints = [
        ("/schedule/groups/{group_id}", "get"),
        ("/schedule/teachers/{teacher_id}", "get"),
        ("/schedule/rooms/{room_id}", "get"),
    ]

    for path, method in endpoints:
        responses = _responses(schema, path, method)

        assert "422" in responses
        schema_ref = responses["422"]["content"]["application/json"]["schema"]["$ref"]
        assert schema_ref == "#/components/schemas/ApiErrorResponse"


def test_schedule_read_endpoints_document_pagination() -> None:
    schema = _openapi_schema()
    endpoints = [
        ("/schedule/groups/{group_id}", "get"),
        ("/schedule/teachers/{teacher_id}", "get"),
        ("/schedule/rooms/{room_id}", "get"),
    ]

    for path, method in endpoints:
        operation = schema["paths"][path][method]
        parameter_names = {parameter["name"] for parameter in operation["parameters"]}
        response_schema_ref = operation["responses"]["200"]["content"][
            "application/json"
        ]["schema"]["$ref"]

        assert {"limit", "offset"}.issubset(parameter_names)
        assert response_schema_ref == "#/components/schemas/ScheduleEntryPage"


def test_schedule_read_endpoints_document_explicit_filters() -> None:
    schema = _openapi_schema()

    group_query_params = _query_parameter_names(
        schema,
        "/schedule/groups/{group_id}",
        "get",
    )
    teacher_query_params = _query_parameter_names(
        schema,
        "/schedule/teachers/{teacher_id}",
        "get",
    )
    room_query_params = _query_parameter_names(
        schema,
        "/schedule/rooms/{room_id}",
        "get",
    )

    assert {"subject_id", "teacher_id", "room_id"}.issubset(group_query_params)
    assert {"subject_id", "room_id"}.issubset(teacher_query_params)
    assert {"subject_id", "teacher_id"}.issubset(room_query_params)

    assert "group_id" not in group_query_params
    assert "teacher_id" not in teacher_query_params
    assert "room_id" not in room_query_params


def test_schedule_endpoint_summaries_are_stable() -> None:
    schema = _openapi_schema()
    expected_summaries = {
        ("/schedule/entries", "post"): "Create schedule entry",
        ("/schedule/entries/{entry_id}", "put"): "Update schedule entry",
        ("/schedule/entries/{entry_id}/cancel", "post"): "Cancel schedule entry",
        (
            "/schedule/entries/{entry_id}/replace",
            "post",
        ): "Replace or move schedule entry",
        (
            "/schedule/entries/{entry_id}/history",
            "get",
        ): "Get schedule entry history",
        ("/schedule/groups/{group_id}", "get"): "Get group schedule",
        ("/schedule/teachers/{teacher_id}", "get"): "Get teacher schedule",
        ("/schedule/rooms/{room_id}", "get"): "Get room schedule",
    }

    for (path, method), summary in expected_summaries.items():
        assert schema["paths"][path][method]["summary"] == summary


def test_lookup_endpoints_are_documented() -> None:
    schema = _openapi_schema()
    expected = {
        "/lookup/groups": ("List group lookup items", "GroupLookupItem"),
        "/lookup/teachers": ("List teacher lookup items", "TeacherLookupItem"),
        "/lookup/rooms": ("List room lookup items", "RoomLookupItem"),
        "/lookup/subjects": ("List subject lookup items", "SubjectLookupItem"),
    }

    for path, (summary, schema_name) in expected.items():
        operation = schema["paths"][path]["get"]
        response_schema = operation["responses"]["200"]["content"][
            "application/json"
        ]["schema"]

        assert operation["summary"] == summary
        assert response_schema["type"] == "array"
        assert response_schema["items"]["$ref"] == (
            f"#/components/schemas/{schema_name}"
        )
