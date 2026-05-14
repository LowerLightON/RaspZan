from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from app.core.errors import AppError
from app.schemas.errors import ApiError, ApiErrorResponse


HTTP_EXCEPTION_CODES = {
    status.HTTP_400_BAD_REQUEST: "bad_request",
    status.HTTP_401_UNAUTHORIZED: "unauthorized",
    status.HTTP_403_FORBIDDEN: "forbidden",
    status.HTTP_404_NOT_FOUND: "not_found",
}


def _error_response(
    *,
    status_code: int,
    code: str,
    message: str,
    details: dict | None = None,
) -> JSONResponse:
    body = ApiErrorResponse(
        error=ApiError(
            code=code,
            message=message,
            details=details or {},
        )
    )
    return JSONResponse(
        status_code=status_code,
        content=jsonable_encoder(body),
    )


async def app_error_handler(
    request: Request,
    exc: AppError,
) -> JSONResponse:
    return _error_response(
        status_code=exc.status_code,
        code=exc.code,
        message=exc.message,
        details=exc.details,
    )


async def http_exception_handler(
    request: Request,
    exc: HTTPException,
) -> JSONResponse:
    code = HTTP_EXCEPTION_CODES.get(exc.status_code, "http_error")
    message = exc.detail if isinstance(exc.detail, str) else "HTTP error"
    details = {} if isinstance(exc.detail, str) else {"detail": exc.detail}

    return _error_response(
        status_code=exc.status_code,
        code=code,
        message=message,
        details=details,
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    return _error_response(
        status_code=422,
        code="validation_error",
        message="Request validation failed",
        details={"errors": exc.errors()},
    )


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
