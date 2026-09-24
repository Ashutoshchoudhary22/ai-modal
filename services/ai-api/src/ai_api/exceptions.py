"""Exception handlers."""

from __future__ import annotations

from ai_platform_protocol.models.common import ErrorDetail, ErrorResponse
from ai_platform_protocol.models.errors import ProviderErrorCode
from ai_platform_shared.logging import get_logger
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from ai_api.providers.errors import ProviderError

logger = get_logger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(ProviderError)
    async def provider_error_handler(request: Request, exc: ProviderError) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        logger.error(
            "provider error | request_id=%s | code=%s | message=%s",
            request_id,
            exc.code,
            exc.message,
        )
        payload = ErrorResponse(
            error=ErrorDetail(code=str(exc.code), message=exc.message, details=exc.details),
            request_id=request_id,
        )
        return JSONResponse(status_code=exc.status_code, content=payload.model_dump())

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        payload = ErrorResponse(
            error=ErrorDetail(
                code=str(ProviderErrorCode.VALIDATION_ERROR),
                message="Invalid request payload",
                details={"errors": exc.errors()},
            ),
            request_id=request_id,
        )
        return JSONResponse(status_code=422, content=payload.model_dump())

    @app.exception_handler(ValidationError)
    async def pydantic_validation_handler(request: Request, exc: ValidationError) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        payload = ErrorResponse(
            error=ErrorDetail(
                code=str(ProviderErrorCode.VALIDATION_ERROR),
                message="Invalid request payload",
                details={"errors": exc.errors()},
            ),
            request_id=request_id,
        )
        return JSONResponse(status_code=422, content=payload.model_dump())

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        logger.exception("unhandled error | request_id=%s", request_id)
        payload = ErrorResponse(
            error=ErrorDetail(
                code=str(ProviderErrorCode.INTERNAL_ERROR),
                message="Internal server error",
            ),
            request_id=request_id,
        )
        return JSONResponse(status_code=500, content=payload.model_dump())
