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


class IStorageService(Protocol):
    """ストレージサービスのインターフェース。"""

    def upload(self, file_path: str, key: str) -> str:
        """ファイルをアップロードします。

        Args:
            file_path (str): アップロード元のローカルファイルパス
            key (str): 保存先のキー (ファイル名)

        Returns:
            str: アップロードされたリソースへの識別子 (キーやURLの一部)
        """
        ...

    def generate_signed_url(self, key: str, expires_in: int = 3600) -> str:
        """署名付き URL を生成します。

        Args:
            key (str): 対象のキー
            expires_in (int): 有効期限 (秒)

        Returns:
            str: 生成された署名付き URL
        """
        ...


class IVideoSink(Protocol):
    """動画出力のインターフェース。"""

    def save_video(
        self,
        frames: Iterator[NDArray[np.uint8]],
        output_path: str,
        fps: float,
        audio_path: str | None = None,
    ) -> None:
        """フレーム列を動画ファイルとして保存します。

        Args:
            frames (Iterator[NDArray[np.uint8]]): 画像データのイテレータ
            output_path (str): 出力先ファイルパス
            fps (float): フレームレート
            audio_path (str | None): 音声ソースとなる動画/音声ファイルのパス
        """
        ...
