from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import RedirectResponse


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
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/", include_in_schema=False)
def read_root() -> RedirectResponse:
    """ルートパスへのアクセスを API ドキュメントへリダイレクトします。"""
    return RedirectResponse(url="/docs")


@app.get("/health")
def health_check() -> dict[str, str]:
    """サービスの健全性を確認するヘルスチェックエンドポイント。

    Returns:
        dict[str, str]: サービスのステータス (例: {"status": "ok"})

    """
    return {"status": "ok"}
