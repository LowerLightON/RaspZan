from typing import Any

from app.schemas.errors import ApiErrorResponse


def _error_response(
    description: str,
    examples: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    return {
        "model": ApiErrorResponse,
        "description": description,
        "content": {
            "application/json": {
                "examples": examples,
            },
        },
    }


VALIDATION_ERROR_RESPONSE = _error_response(
    "Request validation failed.",
    {
        "validation_error": {
            "summary": "Invalid request",
            "value": {
                "error": {
                    "code": "validation_error",
                    "message": "Request validation failed",
                    "details": {
                        "errors": [
                            {
                                "type": "missing",
                                "loc": ["body", "entry_type"],
                                "msg": "Field required",
                                "input": {},
                            }
                        ]
                    },
                }
            },
        }
    },
)

SCHEDULE_WRITE_ERROR_RESPONSES = {
    401: _error_response(
        "Authentication failed for the X-User-Id header.",
        {
            "missing_user_header": {
                "summary": "Missing user header",
                "value": {
                    "error": {
                        "code": "missing_user_header",
                        "message": "X-User-Id header is required",
                        "details": {},
                    }
                },
            },
            "invalid_user_header": {
                "summary": "Invalid user header",
                "value": {
                    "error": {
                        "code": "invalid_user_header",
                        "message": "X-User-Id header must be an integer",
                        "details": {},
                    }
                },
            },
            "user_not_found": {
                "summary": "Unknown user",
                "value": {
                    "error": {
                        "code": "user_not_found",
                        "message": "User not found",
                        "details": {},
                    }
                },
            },
        },
    ),
    403: _error_response(
        "The authenticated user cannot modify schedule entries.",
        {
            "inactive_user": {
                "summary": "Inactive user",
                "value": {
                    "error": {
                        "code": "inactive_user",
                        "message": "User is inactive",
                        "details": {},
                    }
                },
            },
            "schedule_write_forbidden": {
                "summary": "Schedule write forbidden",
                "value": {
                    "error": {
                        "code": "schedule_write_forbidden",
                        "message": "User is not allowed to modify schedule",
                        "details": {},
                    }
                },
            },
        },
    ),
    422: VALIDATION_ERROR_RESPONSE,
}

SCHEDULE_READ_ERROR_RESPONSES = {
    422: VALIDATION_ERROR_RESPONSE,
}

SCHEDULE_HISTORY_ERROR_RESPONSES = {
    404: _error_response(
        "The requested schedule entry was not found.",
        {
            "schedule_not_found": {
                "summary": "Schedule entry not found",
                "value": {
                    "error": {
                        "code": "schedule_not_found",
                        "message": "Schedule entry not found",
                        "details": {},
                    }
                },
            }
        },
    ),
    422: VALIDATION_ERROR_RESPONSE,
}
