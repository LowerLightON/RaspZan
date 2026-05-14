from pydantic import BaseModel, ConfigDict, Field


class ApiError(BaseModel):
    code: str
    message: str
    details: dict = Field(default_factory=dict)


class ApiErrorResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": {
                    "code": "validation_error",
                    "message": "Request validation failed",
                    "details": {"errors": []},
                }
            }
        }
    )

    error: ApiError
