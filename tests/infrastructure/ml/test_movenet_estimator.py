"""MoveNetPoseEstimator のテスト。

最適化後の実装をテスト:
- 初期化とバリデーション
- 有効な姿勢検出
- 低スコア除外
- 入力バリデーションエラー
"""

from collections.abc import Generator
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from numpy.typing import NDArray

from posture_estimation.domain.exceptions import PoseEstimationError
from posture_estimation.domain.values import KeypointName
from posture_estimation.infrastructure.ml.movenet_estimator import MoveNetPoseEstimator


@pytest.fixture
def mock_tf_hub() -> Generator[MagicMock, None, None]:
    """tensorflow_hub.load のモックフィクスチャ。"""
    with patch("tensorflow_hub.load") as mock:
        mock_model = MagicMock()
        mock.return_value = mock_model

        mock_signature = MagicMock()
        mock_model.signatures = {"serving_default": mock_signature}

        yield mock


def test_movenet_initialization(mock_tf_hub: MagicMock) -> None:
    """MoveNetPoseEstimator の初期化を確認する。"""
    estimator = MoveNetPoseEstimator(
        model_url="http://dummy/model", score_threshold=0.3
    )

    mock_tf_hub.assert_called_once_with("http://dummy/model")
    assert estimator._score_threshold == 0.3


def test_movenet_invalid_threshold() -> None:
    """無効なスコア閾値でエラーが発生することを確認する。"""
    with pytest.raises(ValueError, match="score_threshold must be between"):
        MoveNetPoseEstimator(model_url="http://dummy/model", score_threshold=1.5)


def test_estimate_valid_pose(mock_tf_hub: MagicMock) -> None:
    """有効な姿勢が検出された場合の動作を確認する。"""
    estimator = MoveNetPoseEstimator(
        model_url="http://dummy/model", score_threshold=0.3
    )

    dummy_image: NDArray[np.uint8] = np.zeros((192, 192, 3), dtype=np.uint8)

    mock_output = np.zeros((1, 6, 56), dtype=np.float32)
    for i in range(17):
        mock_output[0, 0, i * 3] = 0.5  # y
        mock_output[0, 0, i * 3 + 1] = 0.5  # x
        mock_output[0, 0, i * 3 + 2] = 0.9  # score

    mock_output[0, 0, 55] = 0.9  # bbox score

    # グラフモード推論関数をモック
    output_tensor = MagicMock()
    output_tensor.numpy.return_value = mock_output
    estimator._inference_fn = MagicMock(return_value=output_tensor)

    poses = estimator.estimate(dummy_image)

    assert len(poses) == 1
    assert len(poses[0].keypoints) == 17
    assert poses[0].keypoints[0].name == KeypointName.NOSE
    assert poses[0].keypoints[0].score == pytest.approx(0.9)
    assert poses[0].overall_score == pytest.approx(0.9)


def test_estimate_filter_low_score(mock_tf_hub: MagicMock) -> None:
    """スコアが低い姿勢が除外されるか確認する。"""
    estimator = MoveNetPoseEstimator(
        model_url="http://dummy/model", score_threshold=0.5
    )

    dummy_image: NDArray[np.uint8] = np.zeros((192, 192, 3), dtype=np.uint8)

    mock_output = np.zeros((1, 6, 56), dtype=np.float32)
    for i in range(17):
        mock_output[0, 0, i * 3 + 2] = 0.1  # low keypoint score
    mock_output[0, 0, 55] = 0.2  # low bbox score

    output_tensor = MagicMock()
    output_tensor.numpy.return_value = mock_output
    estimator._inference_fn = MagicMock(return_value=output_tensor)

    poses = estimator.estimate(dummy_image)

    assert len(poses) == 0


def test_estimate_invalid_input_ndim(mock_tf_hub: MagicMock) -> None:
    """入力画像の次元数が不正な場合にエラーが発生することを確認する。"""
    estimator = MoveNetPoseEstimator(model_url="http://dummy/model")

    invalid_image = np.zeros((192, 192), dtype=np.uint8)  # 2D array

    with pytest.raises(PoseEstimationError, match="Expected 3D array"):
        estimator.estimate(invalid_image)


def test_estimate_invalid_input_channels(mock_tf_hub: MagicMock) -> None:
    """入力画像のチャンネル数が不正な場合にエラーが発生することを確認する。"""
    estimator = MoveNetPoseEstimator(model_url="http://dummy/model")

    invalid_image = np.zeros((192, 192, 4), dtype=np.uint8)  # 4 channels (RGBA)

    with pytest.raises(PoseEstimationError, match="Expected 3 channels"):
        estimator.estimate(invalid_image)


def test_estimate_invalid_input_dtype(mock_tf_hub: MagicMock) -> None:
    """入力画像の dtype が不正な場合にエラーが発生することを確認する。"""
    estimator = MoveNetPoseEstimator(model_url="http://dummy/model")

    invalid_image = np.zeros((192, 192, 3), dtype=np.float32)  # float instead of uint8

    with pytest.raises(PoseEstimationError, match="Expected dtype uint8"):
        estimator.estimate(invalid_image)  # type: ignore[arg-type]
