"""FastAPI 依存関係 (Depends)。"""

from typing import Annotated

from fastapi import Depends

from posture_estimation.application.use_cases import ProcessVideoUseCase
from posture_estimation.core.containers import AppContainer

# コンテナのシングルトンインスタンス
_container: AppContainer | None = None


def get_container() -> AppContainer:
    """DI コンテナを取得します。"""
    global _container
    if _container is None:
        _container = AppContainer()
        # TODO: 設定ファイルから読み込む
        _container.config.from_dict({
            "ml": {
                "model_url": "https://tfhub.dev/google/movenet/multipose/lightning/1",
                "score_threshold": 0.3,
                "target_size": 256,
            },
            "r2": {
                "endpoint_url": "",  # 環境変数から取得
                "access_key": "",
                "secret_key": "",
                "bucket_name": "",
            },
        })
    return _container


def get_process_video_use_case(
    container: Annotated[AppContainer, Depends(get_container)]
) -> ProcessVideoUseCase:
    """ProcessVideoUseCase を取得します。"""
    return container.process_video_use_case()


# 型エイリアス
ProcessVideoUseCaseDep = Annotated[
    ProcessVideoUseCase,
    Depends(get_process_video_use_case)
]
