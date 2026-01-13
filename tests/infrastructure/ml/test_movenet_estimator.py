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
import tensorflow as tf
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
        # MoveNet の出力を模倣する辞書と Tensor を返すように設定
        mock_signature.return_value = {
            "output_0": tf.zeros((1, 6, 56), dtype=tf.float32)
        }
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
    # 期待する推論結果をセットアップ
    mock_output = np.zeros((1, 6, 56), dtype=np.float32)
    for i in range(17):
        mock_output[0, 0, i * 3] = 0.5  # y
        mock_output[0, 0, i * 3 + 1] = 0.5  # x
        mock_output[0, 0, i * 3 + 2] = 0.9  # score
    mock_output[0, 0, 55] = 0.9  # bbox score

    # 初期化前にシグネチャの戻り値を設定
    mock_tf_hub.return_value.signatures["serving_default"].return_value = {
        "output_0": tf.convert_to_tensor(mock_output)
    }

    estimator = MoveNetPoseEstimator(
        model_url="http://dummy/model", score_threshold=0.3
    )

    dummy_image: NDArray[np.uint8] = np.zeros((192, 192, 3), dtype=np.uint8)
    poses = estimator.estimate(dummy_image)

    assert len(poses) == 1
    assert len(poses[0].keypoints) == 17
    assert poses[0].keypoints[0].name == KeypointName.NOSE
    assert poses[0].keypoints[0].score == pytest.approx(0.9)
    assert poses[0].overall_score == pytest.approx(0.9)


def test_estimate_filter_low_score(mock_tf_hub: MagicMock) -> None:
    """スコアが低い姿勢が除外されるか確認する。"""
    mock_output = np.zeros((1, 6, 56), dtype=np.float32)
    for i in range(17):
        mock_output[0, 0, i * 3 + 2] = 0.1  # low keypoint score
    mock_output[0, 0, 55] = 0.2  # low bbox score

    mock_tf_hub.return_value.signatures["serving_default"].return_value = {
        "output_0": tf.convert_to_tensor(mock_output)
    }

    estimator = MoveNetPoseEstimator(
        model_url="http://dummy/model", score_threshold=0.5
    )

    dummy_image: NDArray[np.uint8] = np.zeros((192, 192, 3), dtype=np.uint8)
    poses = estimator.estimate(dummy_image)

    assert len(poses) == 0


def test_estimate_coordinate_transformation(mock_tf_hub: MagicMock) -> None:
    """非正方形の画像で座標が正しく逆変換されるか確認する。"""
    mock_output = np.zeros((1, 6, 56), dtype=np.float32)
    mock_output[0, 0, 0] = 0.5  # y (padded image の中心)
    mock_output[0, 0, 1] = 0.5  # x (padded image の中心)
    mock_output[0, 0, 2] = 0.9  # score
    mock_output[0, 0, 55] = 0.9  # bbox score

    mock_tf_hub.return_value.signatures["serving_default"].return_value = {
        "output_0": tf.convert_to_tensor(mock_output)
    }

    estimator = MoveNetPoseEstimator(
        model_url="http://dummy/model", score_threshold=0.3, target_size=256
    )

    # 128x64 -> target 256x256 では 256x128 にリサイズされ、上下にパディング
    dummy_image: NDArray[np.uint8] = np.zeros((64, 128, 3), dtype=np.uint8)
    poses = estimator.estimate(dummy_image)

    assert poses[0].keypoints[0].point.y == pytest.approx(0.5)
    assert poses[0].keypoints[0].point.x == pytest.approx(0.5)


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
