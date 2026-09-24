"""Provider-specific exceptions."""

from ai_platform_protocol.models.errors import ProviderErrorCode


class ProviderError(Exception):
    def __init__(
        self,
        code: ProviderErrorCode,
        message: str,
        *,
        details: dict[str, object] | None = None,
        status_code: int = 400,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}
        self.status_code = status_code


def http_status_for_code(code: ProviderErrorCode) -> int:
    mapping = {
        ProviderErrorCode.MODEL_NOT_CONFIGURED: 503,
        ProviderErrorCode.MODEL_NOT_FOUND: 404,
        ProviderErrorCode.MODEL_LOAD_FAILED: 503,
        ProviderErrorCode.CUDA_UNAVAILABLE: 503,
        ProviderErrorCode.OUT_OF_MEMORY: 503,
        ProviderErrorCode.CONTEXT_LENGTH_EXCEEDED: 400,
        ProviderErrorCode.INVALID_REQUEST: 400,
        ProviderErrorCode.PROVIDER_UNAVAILABLE: 503,
        ProviderErrorCode.GENERATION_TIMEOUT: 504,
        ProviderErrorCode.GENERATION_CANCELLED: 499,
        ProviderErrorCode.VALIDATION_ERROR: 422,
        ProviderErrorCode.INTERNAL_ERROR: 500,
    }
    return mapping.get(code, 400)
