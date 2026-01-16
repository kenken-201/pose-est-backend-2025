"""API ミドルウェア。"""

import logging
import os
import secrets
import time

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class CloudflareAuthMiddleware(BaseHTTPMiddleware):
    """Cloudflare からのアクセスを認証するミドルウェア。"""

    def __init__(self, app: ASGIApp) -> None:
        """ミドルウェアを初期化します。"""
        super().__init__(app)
        # 起動時にトークンを読み込み (アクセスごとに os.getenv しない)
        self.expected_token = os.getenv("CLOUDFLARE_ACCESS_TOKEN")
        if not self.expected_token:
            logger.warning("CLOUDFLARE_ACCESS_TOKEN is not set. Auth is disabled.")

    async def dispatch(self, request: Request, call_next: object) -> Response:
        """リクエストヘッダーのトークンを検証します。"""
        # トークンが設定されていない場合は認証をスキップ (ローカル開発用など)
        if not self.expected_token:
            return await call_next(request)  # type: ignore

        # Preflight Request (OPTIONS) は除外
        if request.method == "OPTIONS":
            return await call_next(request)  # type: ignore

        # ヘルスチェックエンドポイントは除外
        if request.url.path.endswith("/health"):
            return await call_next(request)  # type: ignore

        # トークン検証
        request_token = request.headers.get("X-CF-Access-Token") or ""

        # タイミング攻撃耐性のある比較を使用
        if not secrets.compare_digest(request_token, self.expected_token):
            client_ip = request.client.host if request.client else "unknown"
            logger.warning(f"Unauthorized access blocked from {client_ip}")
            return JSONResponse(
                status_code=403, content={"detail": "Forbidden: Invalid access token"}
            )

        return await call_next(request)  # type: ignore


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
