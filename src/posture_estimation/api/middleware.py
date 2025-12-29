"""API ミドルウェア。"""

import logging
import time

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """リクエスト/レスポンスのログを記録するミドルウェア。"""

    async def dispatch(self, request: Request, call_next: object) -> Response:
        """リクエストを処理し、ログを記録します。"""
        start_time = time.time()

        # リクエスト情報
        method = request.method
        path = request.url.path
        client = request.client.host if request.client else "unknown"

        logger.info("Request: %s %s from %s", method, path, client)

        # 次のミドルウェア/ハンドラーを呼び出し
        response: Response = await call_next(request)  # type: ignore

        # 処理時間計算
        duration = time.time() - start_time

        # レスポンスログ
        logger.info(
            "Response: %s %s - %d (%0.2fs)",
            method,
            path,
            response.status_code,
            duration,
        )

        # レスポンスヘッダーに処理時間を追加
        response.headers["X-Process-Time"] = f"{duration:.3f}"

        return response
