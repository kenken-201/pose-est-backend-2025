from unittest.mock import patch

import pytest

from posture_estimation.application.use_cases import ProcessVideoUseCase
from posture_estimation.core.containers import AppContainer


@pytest.fixture
def container() -> AppContainer:
    """DI コンテナのフィクスチャ (テスト用設定済み)。"""
    container = AppContainer()
    container.config.from_dict({
        "ml": {
            "model_url": "http://dummy",
            "score_threshold": 0.3,
            "target_size": 192,
        },
        "r2": {
            "endpoint_url": "http://r2",
            "access_key": "key",
            "secret_key": "secret",
            "bucket_name": "bucket",
        },
    })
    return container


def test_process_video_use_case_wiring(container: AppContainer) -> None:
    """ProcessVideoUseCase が正しく生成されることを確認する。"""
    # 外部依存をモック化 (特に重い初期化処理があるもの)
    with patch("posture_estimation.infrastructure.ml.movenet_estimator.hub.load"), \
         patch("posture_estimation.infrastructure.ml.movenet_estimator.MoveNetPoseEstimator._warmup"), \
         patch("posture_estimation.infrastructure.storage.r2_service.boto3.client"):

        use_case = container.process_video_use_case()

        assert isinstance(use_case, ProcessVideoUseCase)
        assert use_case._pose_estimator is not None
        assert use_case._storage_service is not None
