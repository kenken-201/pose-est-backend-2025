"""MoveNet (MultiPose) を使用した姿勢推定エンジン。

最適化ポイント:
- @tf.function によるグラフモード実行 (推論高速化)
- NumPy ベクトル化によるキーポイント解析 (Python ループ回避)
- 入力バリデーション (早期エラー検出)
"""

from typing import Any, Final

import cv2
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
_DEFAULT_TARGET_SIZE: Final[int] = 256


class MoveNetPoseEstimator(IPoseEstimator):
    """MoveNet (MultiPose) を使用した姿勢推定エンジン。

    特徴:
    - TensorFlow Graph Mode による高速推論
    - Letterboxing によるアスペクト比を維持したリサイズ
    - Warm-up による初回推論遅延の解消
    - NumPy ベクトル化によるキーポイント処理
    - 複数人検出対応 (最大6人)
    """

    def __init__(
        self,
        model_url: str,
        score_threshold: float = 0.2,
        target_size: int = _DEFAULT_TARGET_SIZE,
    ) -> None:
        """初期化。

        Args:
            model_url: TensorFlow Hub のモデル URL
            score_threshold: 姿勢検出の閾値 (0.0-1.0)
            target_size: 推論時の入力サイズ (32の倍数を推奨)

        Raises:
            ValueError: score_threshold が 0.0-1.0 の範囲外の場合
        """
        if not 0.0 <= score_threshold <= 1.0:
            msg = f"score_threshold must be between 0.0 and 1.0, got {score_threshold}"
            raise ValueError(msg)

        self._model = hub.load(model_url)
        self._movenet = self._model.signatures["serving_default"]
        self._score_threshold = score_threshold
        self._target_size = target_size

        # 推論関数をグラフモードでコンパイル (初回呼び出し時にトレース)
        self._inference_fn = self._create_inference_function()

        # Warm-up: ダミー入力でグラフをコンパイルさせておく
        self._warmup()

    def _warmup(self) -> None:
        """ダミーデータを用いてモデルをウォームアップ。"""
        dummy_input = tf.zeros(
            [1, self._target_size, self._target_size, 3], dtype=tf.int32
        )
        self._inference_fn(dummy_input)

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

    def _preprocess(
        self, image: NDArray[np.uint8]
    ) -> tuple[tf.Tensor, dict[str, float]]:
        """画像の前処理 (Letterboxing)。

        アスペクト比を維持したままリサイズし、パディングを行います。

        Args:
            image: 元画像 (H, W, 3)

        Returns:
            (input_tensor, pad_info): 入力テンソルとパディング情報のタプル
        """
        h_orig, w_orig = image.shape[:2]

        # スケール計算
        scale = self._target_size / max(h_orig, w_orig)
        h_new, w_new = int(h_orig * scale), int(w_orig * scale)

        # アスペクト比維持リサイズ
        resized = cv2.resize(image, (w_new, h_new), interpolation=cv2.INTER_LINEAR)

        # パディング (中央配置)
        pad_y = (self._target_size - h_new) // 2
        pad_x = (self._target_size - w_new) // 2

        padded = np.zeros(
            (self._target_size, self._target_size, 3), dtype=np.uint8
        )
        padded[pad_y : pad_y + h_new, pad_x : pad_x + w_new, :] = resized

        # テンソル変換
        input_tensor = tf.cast(padded, dtype=tf.int32)
        input_tensor = tf.expand_dims(input_tensor, axis=0)

        # 後処理用の情報
        pad_info = {
            "pad_y_ratio": pad_y / self._target_size,
            "pad_x_ratio": pad_x / self._target_size,
            "h_new_ratio": h_new / self._target_size,
            "w_new_ratio": w_new / self._target_size,
        }

        return input_tensor, pad_info

    def _parse_keypoints_vectorized(
        self,
        keypoints_data: NDArray[np.floating[Any]],
        pad_info: dict[str, float],
    ) -> list[Keypoint]:
        """NumPy ベクトル化によるキーポイント解析。

        Letterboxing によるパディングを考慮して元の座標系に逆変換します。

        Args:
            keypoints_data: キーポイントデータ [17, 3] (y, x, score)
            pad_info: 前処理時のパディング情報

        Returns:
            パースされたキーポイントリスト
        """
        y_padded = keypoints_data[:, 0]
        x_padded = keypoints_data[:, 1]
        scores = keypoints_data[:, 2]

        # パディングを除去して元の正規化座標 (0.0-1.0) に変換
        y_orig = (y_padded - pad_info["pad_y_ratio"]) / pad_info["h_new_ratio"]
        x_orig = (x_padded - pad_info["pad_x_ratio"]) / pad_info["w_new_ratio"]

        # 範囲外をクリップ
        y_orig = np.clip(y_orig, 0.0, 1.0)
        x_orig = np.clip(x_orig, 0.0, 1.0)

        return [
            Keypoint(
                name=KEYPOINT_ORDER[idx],
                point=Point2D(x=float(x_orig[idx]), y=float(y_orig[idx])),
                score=float(scores[idx]),
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

        # 前処理 (Letterboxing)
        input_tensor, pad_info = self._preprocess(image)

        # グラフモードで推論実行
        output_tensor = self._inference_fn(input_tensor)
        keypoints_with_scores: NDArray[np.floating[Any]] = (
            output_tensor.numpy()
        )

        # 結果解析
        results: list[Pose] = []
        instances = keypoints_with_scores[0]  # バッチ次元を除去 [6, 56]

        for instance in instances:
            # bbox_score による早期フィルタリング
            bbox_score = float(instance[_BBOX_SCORE_INDEX])
            if bbox_score < self._score_threshold:
                continue

            # キーポイント解析 (逆変換含むベクトル化)
            keypoints_raw = instance[:_KEYPOINT_DATA_SIZE].reshape(
                (_NUM_KEYPOINTS, 3)
            )
            parsed_keypoints = self._parse_keypoints_vectorized(
                keypoints_raw, pad_info
            )

            results.append(
                Pose(
                    frame_index=0,
                    keypoints=parsed_keypoints,
                    overall_score=bbox_score,
                )
            )

        return results
