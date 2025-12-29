from collections.abc import Generator
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from numpy.typing import NDArray

from posture_estimation.domain.values import KeypointName
from posture_estimation.infrastructure.ml.movenet_estimator import MoveNetPoseEstimator


@pytest.fixture
def mock_tf_hub() -> Generator[MagicMock, None, None]:
    """tensorflow_hub.load のモックフィクスチャ。"""
    with patch("tensorflow_hub.load") as mock:
        # モックモデルの振る舞いを定義
        # MoveNet の出力: [1, 6, 56] (batch, instance, keypoints)
        # 56 = 17 * 3 (y, x, score) + 5 (bounding box score + box ymin, xmin, ymax, xmax)
        # ここでは簡略化のため、直接この形状を返すようにモックする
        mock_model = MagicMock()
        mock.return_value = mock_model

        # モックの推論メソッド (m.signatures['serving_default'])
        mock_signature = MagicMock()
        mock_model.signatures = {"serving_default": mock_signature}

        yield mock


def test_movenet_initialization(mock_tf_hub: MagicMock) -> None:
    """MoveNetPoseEstimator の初期化を確認する。"""
    estimator = MoveNetPoseEstimator(model_url="http://dummy/model", score_threshold=0.3)

    mock_tf_hub.assert_called_once_with("http://dummy/model")
    assert estimator.score_threshold == 0.3


def test_estimate_valid_pose(mock_tf_hub: MagicMock) -> None:
    """有効な姿勢が検出された場合の動作を確認する。"""
    estimator = MoveNetPoseEstimator(model_url="http://dummy/model", score_threshold=0.3)

    # ダミー入力画像 192x192x3
    dummy_image: NDArray[np.uint8] = np.zeros((192, 192, 3), dtype=np.uint8)

    # ダミー出力: 1人分の検出結果
    # [1, 6, 56]
    # 最初のインスタンス: 全て 0.5 の座標と 0.9 のスコア
    # 56要素のうち、最初の51要素が (y, x, score) * 17
    mock_output = np.zeros((1, 6, 56), dtype=np.float32)

    # 1人目のキーポイント (y, x, score)
    for i in range(17):
        mock_output[0, 0, i * 3] = 0.5      # y
        mock_output[0, 0, i * 3 + 1] = 0.5  # x
        mock_output[0, 0, i * 3 + 2] = 0.9  # score

    # bbox score (index 55) を設定
    mock_output[0, 0, 55] = 0.9

    # モックの推論結果を設定
    mock_signature = mock_tf_hub.return_value.signatures["serving_default"]

    # .numpy() メソッドを持つオブジェクトを作成
    output_tensor = MagicMock()
    output_tensor.numpy.return_value = mock_output

    mock_signature.return_value = {"output_0": output_tensor}

    poses = estimator.estimate(dummy_image)

    assert len(poses) == 1
    assert len(poses[0].keypoints) == 17
    assert poses[0].keypoints[0].name == KeypointName.NOSE
    assert poses[0].keypoints[0].score == pytest.approx(0.9)
    # overall_score の計算ロジックに依存するが、ここでは単純平均などを想定
    assert poses[0].overall_score > 0.0


def test_estimate_filter_low_score(mock_tf_hub: MagicMock) -> None:
    """スコアが低い姿勢が除外されるか確認する。"""
    estimator = MoveNetPoseEstimator(model_url="http://dummy/model", score_threshold=0.5)

    dummy_image: NDArray[np.uint8] = np.zeros((192, 192, 3), dtype=np.uint8)

    # ダミー出力: 低スコアの検出結果
    mock_output = np.zeros((1, 6, 56), dtype=np.float32)
    # 1人目: スコア 0.1
    for i in range(17):
        mock_output[0, 0, i * 3 + 2] = 0.1

    mock_signature = mock_tf_hub.return_value.signatures["serving_default"]

    output_tensor = MagicMock()
    output_tensor.numpy.return_value = mock_output
    mock_signature.return_value = {"output_0": output_tensor}

    poses = estimator.estimate(dummy_image)

    assert len(poses) == 0
