from fastapi import status


class AppError(Exception):
    def __init__(
        self,
        *,
        status_code: int,
        code: str,
        message: str,
        details: dict | None = None,
    ) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(message)


class UnauthorizedError(AppError):
    def __init__(
        self,
        *,
        code: str,
        message: str,
        details: dict | None = None,
    ) -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code=code,
            message=message,
            details=details,
        )


class ForbiddenError(AppError):
    def __init__(
        self,
        *,
        code: str,
        message: str,
        details: dict | None = None,
    ) -> None:
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            code=code,
            message=message,
            details=details,
        )


class NotFoundError(AppError):
    def __init__(
        self,
        *,
        code: str,
        message: str,
        details: dict | None = None,
    ) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code=code,
            message=message,
            details=details,
        )
