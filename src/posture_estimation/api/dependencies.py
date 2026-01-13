"""FastAPI 依存関係 (Depends)。"""

import os
from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from posture_estimation.application.use_cases import ProcessVideoUseCase
from posture_estimation.core.containers import AppContainer
from posture_estimation.infrastructure.storage.temp_manager import TempFileManager
from posture_estimation.infrastructure.video.opencv_source import OpenCVVideoSource

# 設定定数
DEFAULT_ML_MODEL_URL = "https://tfhub.dev/google/movenet/multipose/lightning/1"
DEFAULT_ML_SCORE_THRESHOLD = 0.3
DEFAULT_ML_TARGET_SIZE = 256
DEFAULT_MAX_UPLOAD_SIZE_MB = 100

# コンテナのシングルトンインスタンス
_container: AppContainer | None = None


@lru_cache
def get_settings() -> dict[str, dict[str, str | float | int]]:
    """環境変数から設定を読み込みます。"""
    return {
        "ml": {
            "model_url": os.getenv("ML_MODEL_URL", DEFAULT_ML_MODEL_URL),
            "score_threshold": float(
                os.getenv("ML_SCORE_THRESHOLD", str(DEFAULT_ML_SCORE_THRESHOLD))
            ),
            "target_size": int(
                os.getenv("ML_TARGET_SIZE", str(DEFAULT_ML_TARGET_SIZE))
            ),
        },
        "r2": {
            "endpoint_url": os.getenv("R2_ENDPOINT_URL", ""),
            "access_key": os.getenv("R2_ACCESS_KEY", ""),
            "secret_key": os.getenv("R2_SECRET_KEY", ""),
            "bucket_name": os.getenv("R2_BUCKET_NAME", ""),
        },
    }


def get_container() -> AppContainer:
    """DI コンテナを取得します。"""
    global _container
    if _container is None:
        _container = AppContainer()
        _container.config.from_dict(get_settings())
    return _container


def get_process_video_use_case(
    container: Annotated[AppContainer, Depends(get_container)],
) -> ProcessVideoUseCase:
    """ProcessVideoUseCase を取得します。"""
    return container.process_video_use_case()


def get_temp_manager() -> TempFileManager:
    """一時ファイルマネージャを取得します。"""
    return TempFileManager()


def get_max_upload_size_bytes() -> int:
    """最大アップロードサイズ (バイト) を取得します。"""
    max_mb = int(os.getenv("MAX_UPLOAD_SIZE_MB", str(DEFAULT_MAX_UPLOAD_SIZE_MB)))
    return max_mb * 1024 * 1024


# 型エイリアス
ProcessVideoUseCaseDep = Annotated[
    ProcessVideoUseCase, Depends(get_process_video_use_case)
]

TempManagerDep = Annotated[TempFileManager, Depends(get_temp_manager)]


def create_video_source(video_path: str) -> OpenCVVideoSource:
    """動画ソースを生成します。"""
    return OpenCVVideoSource(video_path)
