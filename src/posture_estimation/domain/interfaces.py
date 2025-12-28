from collections.abc import Iterator
from typing import Protocol

import numpy as np
from numpy.typing import NDArray

from posture_estimation.domain.entities import AnalyzedVideo, Pose
from posture_estimation.domain.values import VideoMeta


class IPoseEstimator(Protocol):
    """姿勢推定エンジンのインターフェース。"""

    def estimate(self, image: NDArray[np.uint8]) -> list[Pose]:
        """画像から姿勢を推定します。

        Args:
            image (NDArray[np.uint8]): 入力画像 (NumPy配列)

        Returns:
            list[Pose]: 推定された姿勢のリスト
        """
        ...


class IVideoSource(Protocol):
    """動画入力ソースのインターフェース。"""

    def get_meta(self) -> VideoMeta:
        """動画のメタデータを取得します。

        Returns:
            VideoMeta: 動画メタデータ
        """
        ...

    def read_frames(self) -> Iterator[tuple[int, NDArray[np.uint8]]]:
        """動画フレームを順次読み込みます。

        Returns:
            Iterator[tuple[int, NDArray[np.uint8]]]: フレームインデックスと画像データのタプルを返すイテレータ
        """
        ...


class IRepository(Protocol):
    """解析結果の保存・取得を行うリポジトリのインターフェース。"""

    def save(self, analysis: AnalyzedVideo) -> None:
        """解析結果を保存します。

        Args:
            analysis (AnalyzedVideo): 保存する解析結果
        """
        ...
