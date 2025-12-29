"""API 例外とエラーハンドラー。"""

from enum import Enum
from typing import Any

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse


class AppErrorCode(str, Enum):
    """アプリケーションエラーコード。"""

    # 400 Bad Request
    INVALID_VIDEO_FORMAT = "INVALID_VIDEO_FORMAT"
    VIDEO_TOO_SHORT = "VIDEO_TOO_SHORT"
    VIDEO_TOO_LONG = "VIDEO_TOO_LONG"

    # 413 Payload Too Large
    FILE_TOO_LARGE = "FILE_TOO_LARGE"

    # 422 Unprocessable Entity
    INVALID_PARAMETER = "INVALID_PARAMETER"

    # 500 Internal Server Error
    MODEL_INFERENCE_ERROR = "MODEL_INFERENCE_ERROR"

    # 503 Service Unavailable
    STORAGE_SERVICE_UNAVAILABLE = "STORAGE_SERVICE_UNAVAILABLE"


# 動画時間制限 (秒)
MIN_VIDEO_DURATION_SEC = 3.0
MAX_VIDEO_DURATION_SEC = 420.0  # 7分


class APIError(HTTPException):
    """API エラー基底クラス。"""

    def __init__(
        self,
        status_code: int,
        error_code: AppErrorCode,
        message: str,
    ) -> None:
        """初期化。

        Args:
            status_code: HTTP ステータスコード
            error_code: アプリケーションエラーコード
            message: エラーメッセージ
        """
        self.error_code = error_code
        self.error_message = message
        super().__init__(
            status_code=status_code,
            detail={"code": error_code.value, "message": message},
        )


class InvalidVideoFormatError(APIError):
    """無効な動画フォーマットエラー。"""

    def __init__(self, message: str = "Invalid video format") -> None:
        """初期化。"""
        super().__init__(400, AppErrorCode.INVALID_VIDEO_FORMAT, message)


class VideoTooShortError(APIError):
    """動画が短すぎるエラー。"""

    def __init__(self, duration: float) -> None:
        """初期化。"""
        message = (
            f"Video too short: {duration:.1f}s "
            f"(minimum: {MIN_VIDEO_DURATION_SEC}s)"
        )
        super().__init__(400, AppErrorCode.VIDEO_TOO_SHORT, message)


class VideoTooLongError(APIError):
    """動画が長すぎるエラー。"""

    def __init__(self, duration: float) -> None:
        """初期化。"""
        message = (
            f"Video too long: {duration:.1f}s "
            f"(maximum: {MAX_VIDEO_DURATION_SEC / 60:.0f} minutes)"
        )
        super().__init__(400, AppErrorCode.VIDEO_TOO_LONG, message)


class FileTooLargeError(APIError):
    """ファイルサイズ超過エラー。"""

    def __init__(self, size_mb: float, max_size_mb: float) -> None:
        """初期化。"""
        message = f"File too large: {size_mb:.1f}MB (maximum: {max_size_mb:.0f}MB)"
        super().__init__(413, AppErrorCode.FILE_TOO_LARGE, message)


class InvalidParameterError(APIError):
    """パラメータ不正エラー。"""

    def __init__(self, message: str) -> None:
        """初期化。"""
        super().__init__(422, AppErrorCode.INVALID_PARAMETER, message)


class ModelInferenceError(APIError):
    """モデル推論エラー。"""

    def __init__(self, message: str = "Model inference failed") -> None:
        """初期化。"""
        super().__init__(500, AppErrorCode.MODEL_INFERENCE_ERROR, message)


class StorageServiceUnavailableError(APIError):
    """ストレージサービス利用不可エラー。"""

    def __init__(self, message: str = "Storage service unavailable") -> None:
        """初期化。"""
        super().__init__(503, AppErrorCode.STORAGE_SERVICE_UNAVAILABLE, message)


async def api_error_handler(_request: Request, exc: APIError) -> JSONResponse:
    """APIError のハンドラー。"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail},
    )


def register_exception_handlers(app: Any) -> None:
    """アプリケーションに例外ハンドラーを登録します。

    Args:
        app: FastAPI アプリケーションインスタンス
    """
    app.add_exception_handler(APIError, api_error_handler)
