from typing import Final

import tensorflow as tf
import tensorflow_hub as hub
from numpy.typing import NDArray

from posture_estimation.domain.entities import Pose
from posture_estimation.domain.interfaces import IPoseEstimator
from posture_estimation.domain.values import (
    Keypoint,
    KeypointName,
    Point2D,
)

# MoveNet (COCO) keypoint order
KEYPOINT_ORDER: Final[list[KeypointName]] = [
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
]


class MoveNetPoseEstimator(IPoseEstimator):
    """MoveNet (MultiPose) を使用した姿勢推定エンジン。"""

    def __init__(self, model_url: str, score_threshold: float = 0.2) -> None:
        """初期化。

        Args:
            model_url (str): TensorFlow Hub のモデル URL
            score_threshold (float): 姿勢検出の閾値 (0.0-1.0)
        """
        self.model = hub.load(model_url)
        self.movenet = self.model.signatures["serving_default"]
        self.score_threshold = score_threshold

    def estimate(self, image: NDArray[tf.uint8]) -> list[Pose]:
        """画像から姿勢を推定します。

        Args:
            image (NDArray[np.uint8]): 入力画像 (H, W, 3)

        Returns:
            list[Pose]: 推定された姿勢のリスト
        """
        # Tensor への変換とキャスト
        input_image = tf.cast(image, dtype=tf.int32)
        # バッチ次元の追加: [1, H, W, 3]
        input_image = tf.expand_dims(input_image, axis=0)

        # 推論実行
        # outputs['output_0'] shape: [1, 6, 56]
        # (batch, instance, keypoints)
        outputs = self.movenet(input_image)
        keypoints_with_scores = outputs["output_0"].numpy()

        results: list[Pose] = []

        # バッチサイズは常に1前提
        instances = keypoints_with_scores[0]

        for instance in instances:
            # instance shape: [56]
            # [y_0, x_0, s_0, y_1, x_1, s_1, ..., bbox_ymin, bbox_xmin, bbox_ymax, bbox_xmax, bbox_score]

            # 各キーポイントの抽出 (最初の51要素 = 17 * 3)
            # 各キーポイント: (y, x, score)
            keypoints_data = instance[:51].reshape((17, 3))

            # バウンディングボックスのスコア (最後の要素)
            # multipose の場合、instance 全体のスコアとして使える場合があるが、
            # ここではキーポイントスコアの平均を使用する戦略をとるか、あるいは bbox score を使うか。
            # 今回は、全体のスコアとして、キーポイントの平均スコアを採用する。

            parsed_keypoints: list[Keypoint] = []

            for idx, (y, x, score) in enumerate(keypoints_data):
                kp_name = KEYPOINT_ORDER[idx]

                # クリップして範囲内に収める
                y = max(0.0, min(1.0, float(y)))
                x = max(0.0, min(1.0, float(x)))
                score = max(0.0, min(1.0, float(score)))

                parsed_keypoints.append(
                    Keypoint(
                        name=kp_name,
                        point=Point2D(x=x, y=y),
                        score=score
                    )
                )




            # 閾値フィルタリング(instance 全体の信頼度が低い場合は除外)
            # もしくは、bbox score を使う手もあるが、MoveNet output の 55番目(index 55) が bbox score
            bbox_score = instance[55]

            # ここではシンプルに、全てのキーポイントの平均、あるいは bbox_score の高い方などを採用できるが
            # 一般的に bbox_score がインスタンスの信頼度を表す。
            # しかし、ドメイン要件で「overall_score」を定義しているので、そちらに合わせる。

            if bbox_score < self.score_threshold:
                continue

            results.append(
                Pose(
                    frame_index=0,  # 静止画推定のコンテキストでは0、動画処理時に上書きされる想定
                    keypoints=parsed_keypoints,
                    overall_score=float(bbox_score) # ここでは bbox_score を全体の信頼度とする
                )
            )

        return results
