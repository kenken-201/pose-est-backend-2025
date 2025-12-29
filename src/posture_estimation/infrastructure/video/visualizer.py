"""OpenCV を使用した姿勢描画サービス。

Domain Interface: IPoseVisualizer の実装。
"""

from typing import Final

import cv2
import numpy as np
from numpy.typing import NDArray

from posture_estimation.domain.entities import Pose
from posture_estimation.domain.interfaces import IPoseVisualizer


class OpenCVPoseVisualizer(IPoseVisualizer):
    """OpenCV を使用して画像に姿勢情報を描画します。"""

    # COCO Keypoints の接続関係 (Edges)
    _EDGES: Final[tuple[tuple[int, int], ...]] = (
        (0, 1), (0, 2), (1, 3), (2, 4),  # Face
        (5, 6), (5, 7), (7, 9), (6, 8), (8, 10),  # Arms
        (5, 11), (6, 12), (11, 12),  # Torso
        (11, 13), (13, 15), (12, 14), (14, 16),  # Legs
    )

    # 描画色 (BGR)
    _COLOR: Final[tuple[int, int, int]] = (0, 255, 0)  # Green
    _THICKNESS: Final[int] = 2

    def __init__(self, score_threshold: float = 0.2) -> None:
        """初期化。

        Args:
            score_threshold: 描画対象とする最低キーポイントスコア (デフォルト: 0.2)
        """
        self._score_threshold = score_threshold

    def draw(self, image: NDArray[np.uint8], poses: list[Pose]) -> None:
        """画像に姿勢情報を描画します (In-place)。

        Args:
            image: 対象画像 (BGR/RGB どちらでも描画操作は同じ)
            poses: 描画する姿勢リスト
        """
        height, width = image.shape[:2]

        for pose in poses:
            points: dict[int, tuple[int, int]] = {}

            # 1. キーポイントの描画
            for i, keypoint in enumerate(pose.keypoints):
                # スコアが低いキーポイントはスキップ
                if keypoint.score < self._score_threshold:
                    continue

                # 正規化座標 -> ピクセル座標
                px = int(keypoint.point.x * width)
                py = int(keypoint.point.y * height)

                # 画面外チェック (MoveNetは稀に範囲外を出す可能性あり)
                px = max(0, min(width - 1, px))
                py = max(0, min(height - 1, py))

                points[i] = (px, py)

                cv2.circle(image, (px, py), 4, self._COLOR, -1)

            # 2. スケルトン (エッジ) の描画
            for start_idx, end_idx in self._EDGES:
                if start_idx in points and end_idx in points:
                    cv2.line(
                        image,
                        points[start_idx],
                        points[end_idx],
                        self._COLOR,
                        self._THICKNESS,
                    )
