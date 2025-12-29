from collections.abc import Iterator
from typing import ClassVar

import cv2
import numpy as np
from numpy.typing import NDArray

from posture_estimation.domain.exceptions import VideoProcessingError
from posture_estimation.domain.interfaces import IVideoSource
from posture_estimation.domain.values import VideoMeta


class OpenCVVideoSource(IVideoSource):
    """OpenCV を使用した動画入力ソース。"""

    # プロパティIDの定数マッピング
    PROPS: ClassVar[dict[str, int]] = {
        "width": cv2.CAP_PROP_FRAME_WIDTH,
        "height": cv2.CAP_PROP_FRAME_HEIGHT,
        "fps": cv2.CAP_PROP_FPS,
        "frames": cv2.CAP_PROP_FRAME_COUNT,
    }

    def __init__(self, video_path: str) -> None:
        """初期化。

        Args:
            video_path (str): 動画ファイルのパス
        """
        self.video_path = video_path
        self.cap = cv2.VideoCapture(video_path)

        if not self.cap.isOpened():
            msg = f"Failed to open video: {video_path}"
            raise VideoProcessingError(msg)

    def get_meta(self) -> VideoMeta:
        """動画のメタデータを取得します。

        Returns:
            VideoMeta: 動画メタデータ
        """
        width = int(self.cap.get(self.PROPS["width"]))
        height = int(self.cap.get(self.PROPS["height"]))
        fps = float(self.cap.get(self.PROPS["fps"]))
        total_frames = int(self.cap.get(self.PROPS["frames"]))

        if fps <= 0:
            # FPS が取得できない場合のフォールバック(例: 30.0)
            # ここでは厳格にエラーとするか、デフォルト値を使うか要検討。一旦デフォルト。
            fps = 30.0

        duration_sec = total_frames / fps if total_frames > 0 and fps > 0 else 0.0

        # Note: OpenCV 単体では音声の有無を正確に判定するのは難しいため、
        # 後続の FFmpeg 処理でハンドルするか、別途 ffmpeg-python probe を使う。
        # ここでは False (不明/未確認) としておくか、デフォルト True とするか。
        # 要件「音声保持」のため、基本はあるものとして扱う方が安全かもしれないが、
        # ValueObject の init 時に False デフォルトなので、そのままにする。
        # 必要に応じて FFmpeg probe を実装する。
        has_audio = False

        return VideoMeta(
            width=width,
            height=height,
            fps=fps,
            total_frames=total_frames,
            duration_sec=duration_sec,
            has_audio=has_audio,
        )

    def read_frames(self) -> Iterator[tuple[int, NDArray[np.uint8]]]:
        """動画フレームを順次読み込みます。

        Yields:
            Iterator[tuple[int, NDArray[np.uint8]]]: (frame_index, image_rgb)
        """
        frame_idx = 0
        while True:
            ret, frame = self.cap.read()
            if not ret:
                break

            # BGR -> RGB 変換
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB).astype(np.uint8)
            yield frame_idx, frame_rgb
            frame_idx += 1

    def close(self) -> None:
        """リソースを解放します。"""
        if self.cap.isOpened():
            self.cap.release()
