import logging
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from posture_estimation.api.exceptions import register_exception_handlers
from posture_estimation.api.middleware import (
    CloudflareAuthMiddleware,
    RequestLoggingMiddleware,
)
from posture_estimation.api.router import router as api_router

logger = logging.getLogger(__name__)


def _get_cors_origins() -> list[str]:
    """CORS 許可オリジンを取得します。"""
    origins_str = os.getenv("CORS_ORIGINS", "*")
    if origins_str == "*":
        return ["*"]
    return [origin.strip() for origin in origins_str.split(",")]


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """アプリケーションのライフサイクルを管理します。

    MLモデルのロードやDB接続の確立など、起動時の初期化処理と
    終了時のクリーンアップ処理をここに記述します。
    """
    # 起動時の処理 (Startup)
    yield
    # 終了時の処理 (Shutdown)


app = FastAPI(
    title="Pose Estimation Backend",
    description="TensorFlow MoveNet を使用した姿勢推定バックエンド API",
    version="1.0.0",
    lifespan=lifespan,
)

# ログミドルウェア (一番外側: 最後に実行、最初に戻る)
app.add_middleware(RequestLoggingMiddleware)

# CORS ミドルウェア (2番目)
origins = _get_cors_origins()
is_wildcard = origins == ["*"]

if is_wildcard:
    logger.warning(
        "CORS_ORIGINS is set to '*'. allow_credentials is disabled. "
        "For production, specify explicit origins."
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=not is_wildcard,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# 認証ミドルウェア (3番目: CORS の後、アプリの前)
app.add_middleware(CloudflareAuthMiddleware)

# ルーター登録
app.include_router(api_router)

# 例外ハンドラー登録
register_exception_handlers(app)


@app.get("/", include_in_schema=False)
def read_root() -> RedirectResponse:
    """ルートパスへのアクセスを API ドキュメントへリダイレクトします。"""
    return RedirectResponse(url="/docs")
