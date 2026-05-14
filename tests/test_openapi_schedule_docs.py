from fastapi.testclient import TestClient

from app.main import app


def _openapi_schema() -> dict:
    return TestClient(app).get("/openapi.json").json()


def _responses(schema: dict, path: str, method: str) -> dict:
    return schema["paths"][path][method]["responses"]


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
