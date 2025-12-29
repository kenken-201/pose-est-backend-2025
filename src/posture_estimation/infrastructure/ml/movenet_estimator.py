"""MoveNet (MultiPose) を使用した姿勢推定エンジン。

最適化ポイント:
- @tf.function によるグラフモード実行 (推論高速化)
- NumPy ベクトル化によるキーポイント解析 (Python ループ回避)
- 入力バリデーション (早期エラー検出)
"""

from typing import Any, Final

import numpy as np
import tensorflow as tf
import tensorflow_hub as hub
from numpy.typing import NDArray

from posture_estimation.domain.entities import Pose
from posture_estimation.domain.exceptions import PoseEstimationError
from posture_estimation.domain.interfaces import IPoseEstimator
from posture_estimation.domain.values import (
    Keypoint,
    KeypointName,
    Point2D,
)

# MoveNet (COCO) keypoint order
KEYPOINT_ORDER: Final[tuple[KeypointName, ...]] = (
    KeypointName.NOSE,
    KeypointName.LEFT_EYE,
    KeypointName.RIGHT_EYE,
    KeypointName.LEFT_EAR,
    KeypointName.RIGHT_EAR,
    KeypointName.LEFT_SHOULDER,
    KeypointName.RIGHT_SHOULDER,
    KeypointName.LEFT_ELBOW,
    KeypointName.RIGHT_ELBOW,
    KeypointName.LEFT_WRIST,
    KeypointName.RIGHT_WRIST,
    KeypointName.LEFT_HIP,
    KeypointName.RIGHT_HIP,
    KeypointName.LEFT_KNEE,
    KeypointName.RIGHT_KNEE,
    KeypointName.LEFT_ANKLE,
    KeypointName.RIGHT_ANKLE,
)

# MoveNet MultiPose 定数
_NUM_KEYPOINTS: Final[int] = 17
_KEYPOINT_DATA_SIZE: Final[int] = 51  # 17 keypoints * 3 (y, x, score)
_BBOX_SCORE_INDEX: Final[int] = 55


class MoveNetPoseEstimator(IPoseEstimator):
    """MoveNet (MultiPose) を使用した姿勢推定エンジン。

    特徴:
    - TensorFlow Graph Mode による高速推論
    - NumPy ベクトル化によるキーポイント処理
    - 複数人検出対応 (最大6人)
    """

    def __init__(self, model_url: str, score_threshold: float = 0.2) -> None:
        """初期化。

        Args:
            model_url: TensorFlow Hub のモデル URL
            score_threshold: 姿勢検出の閾値 (0.0-1.0)

        Raises:
            ValueError: score_threshold が 0.0-1.0 の範囲外の場合
        """
        if not 0.0 <= score_threshold <= 1.0:
            msg = f"score_threshold must be between 0.0 and 1.0, got {score_threshold}"
            raise ValueError(msg)

        self._model = hub.load(model_url)
        self._movenet = self._model.signatures["serving_default"]
        self._score_threshold = score_threshold

        # 推論関数をグラフモードでコンパイル (初回呼び出し時にトレース)
        self._inference_fn = self._create_inference_function()

    def _create_inference_function(self) -> Any:
        """@tf.function でラップした推論関数を作成。

        Returns:
            グラフモードでコンパイルされた推論関数
        """
        movenet = self._movenet

        @tf.function(reduce_retracing=True)  # type: ignore[untyped-decorator]
        def _run_inference(input_image: tf.Tensor) -> tf.Tensor:
            """TensorFlow グラフモードで推論を実行。

            Args:
                input_image: 入力画像テンソル [1, H, W, 3]

            Returns:
                キーポイント出力テンソル [1, 6, 56]
            """
            outputs = movenet(input_image)
            return outputs["output_0"]

        return _run_inference

    def _validate_input(self, image: NDArray[np.uint8]) -> None:
        """入力画像のバリデーション。

        Args:
            image: 入力画像

        Raises:
            PoseEstimationError: 入力が不正な場合
        """
        if image.ndim != 3:
            msg = f"Expected 3D array (H, W, C), got {image.ndim}D"
            raise PoseEstimationError(msg)

        if image.shape[2] != 3:
            msg = f"Expected 3 channels (RGB), got {image.shape[2]}"
            raise PoseEstimationError(msg)

        if image.dtype != np.uint8:
            msg = f"Expected dtype uint8, got {image.dtype}"
            raise PoseEstimationError(msg)

        if image.shape[0] < 1 or image.shape[1] < 1:
            msg = f"Image dimensions must be positive, got {image.shape[:2]}"
            raise PoseEstimationError(msg)

    def _parse_keypoints_vectorized(
        self, keypoints_data: NDArray[np.floating[Any]]
    ) -> list[Keypoint]:
        """NumPy ベクトル化によるキーポイント解析。

        Args:
            keypoints_data: キーポイントデータ [17, 3] (y, x, score)

        Returns:
            パースされたキーポイントリスト
        """
        # 一括クリッピング (ベクトル化)
        clipped = np.clip(keypoints_data, 0.0, 1.0)

        # リスト内包表記で Keypoint オブジェクト生成
        return [
            Keypoint(
                name=KEYPOINT_ORDER[idx],
                point=Point2D(x=float(clipped[idx, 1]), y=float(clipped[idx, 0])),
                score=float(clipped[idx, 2]),
            )
            for idx in range(_NUM_KEYPOINTS)
        ]

    def estimate(self, image: NDArray[np.uint8]) -> list[Pose]:
        """画像から姿勢を推定します。

        Args:
            image: 入力画像 (H, W, 3), dtype=uint8, 値範囲 0-255

        Returns:
            推定された姿勢のリスト (最大6人)

        Raises:
            PoseEstimationError: 入力画像が不正な場合
        """
        # 入力バリデーション
        self._validate_input(image)

        # TensorFlow への変換 (int32 が MoveNet の期待する型)
        input_tensor = tf.cast(image, dtype=tf.int32)
        input_tensor = tf.expand_dims(input_tensor, axis=0)

        # グラフモードで推論実行
        output_tensor = self._inference_fn(input_tensor)
        keypoints_with_scores: NDArray[np.floating[Any]] = (
            output_tensor.numpy()
        )

        # 結果解析
        results: list[Pose] = []
        instances = keypoints_with_scores[0]  # バッチ次元を除去 [6, 56]

        for instance in instances:
            # bbox_score による早期フィルタリング (パース前に除外)
            bbox_score = float(instance[_BBOX_SCORE_INDEX])
            if bbox_score < self._score_threshold:
                continue

            # キーポイント解析 (ベクトル化)
            keypoints_data = instance[:_KEYPOINT_DATA_SIZE].reshape(
                (_NUM_KEYPOINTS, 3)
            )
            parsed_keypoints = self._parse_keypoints_vectorized(keypoints_data)

            results.append(
                Pose(
                    frame_index=0,  # 動画処理時に上書きされる想定
                    keypoints=parsed_keypoints,
                    overall_score=bbox_score,
                )
            )

        return results
