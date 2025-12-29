from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from posture_estimation.api.exceptions import register_exception_handlers
from posture_estimation.api.router import router as api_router


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

# ルーター登録
app.include_router(api_router)

# 例外ハンドラー登録
register_exception_handlers(app)


@app.get("/", include_in_schema=False)
def read_root() -> RedirectResponse:
    """ルートパスへのアクセスを API ドキュメントへリダイレクトします。"""
    return RedirectResponse(url="/docs")

