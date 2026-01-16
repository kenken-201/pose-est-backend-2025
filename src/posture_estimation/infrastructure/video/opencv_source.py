"""OpenCV を使用した動画入力ソース。

特徴:
- Context Manager サポート (自動リソース解放)
- 詳細なメタデータ取得
- ffprobe による音声トラック検出
- RGB 形式でのフレーム出力
"""

import json
import logging
import subprocess
from collections.abc import Iterator
from types import TracebackType
from typing import ClassVar, Self

import cv2
import numpy as np
from numpy.typing import NDArray

from posture_estimation.domain.exceptions import VideoProcessingError
from posture_estimation.domain.interfaces import IVideoSource
from posture_estimation.domain.values import VideoMeta

logger = logging.getLogger(__name__)


class OpenCVVideoSource(IVideoSource):
    """OpenCV を使用した動画入力ソース。

    Context Manager として使用可能:
    ```python
    with OpenCVVideoSource("video.mp4") as source:
        meta = source.get_meta()
        for frame_idx, frame in source.read_frames():
            process(frame)
    ```
    """

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
            video_path: 動画ファイルのパス

        Raises:
            VideoProcessingError: 動画ファイルを開けない場合
        """
        self.video_path = video_path
        self.cap = cv2.VideoCapture(video_path)

        if not self.cap.isOpened():
            msg = f"Failed to open video: {video_path}"
            raise VideoProcessingError(msg)

    def __enter__(self) -> Self:
        """Context Manager エントリポイント。

        Returns:
            self: インスタンス自身
        """
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Context Manager 終了時にリソースを解放。

        Args:
            exc_type: 例外の型 (あれば)
            exc_val: 例外のインスタンス (あれば)
            exc_tb: トレースバック (あれば)
        """
        self.close()

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
            # FPS が取得できない場合のフォールバック
            fps = 30.0

        duration_sec = total_frames / fps if total_frames > 0 and fps > 0 else 0.0

        # ffprobe を使用して音声トラックの有無を検出
        has_audio = self._detect_audio()

        return VideoMeta(
            width=width,
            height=height,
            fps=fps,
            total_frames=total_frames,
            duration_sec=duration_sec,
            has_audio=has_audio,
        )

    def _detect_audio(self) -> bool:
        """FFprobe を使用して音声トラックの有無を検出します。

        Returns:
            bool: 音声トラックが存在する場合 True
        """
        try:
            result = subprocess.run(  # noqa: S603
                [  # noqa: S607
                    "ffprobe",
                    "-v",
                    "quiet",
                    "-print_format",
                    "json",
                    "-show_streams",
                    "-select_streams",
                    "a",
                    self.video_path,
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode != 0:
                logger.warning(
                    "ffprobe failed for %s, assuming no audio", self.video_path
                )
                return False

            data = json.loads(result.stdout)
            streams = data.get("streams", [])
            has_audio = len(streams) > 0

            logger.debug(
                "Audio detection for %s: %s (streams: %d)",
                self.video_path,
                has_audio,
                len(streams),
            )
            return has_audio

        except FileNotFoundError:
            logger.warning("ffprobe not found, assuming no audio")
            return False
        except subprocess.TimeoutExpired:
            logger.warning("ffprobe timed out for %s", self.video_path)
            return False
        except json.JSONDecodeError:
            logger.warning("Failed to parse ffprobe output for %s", self.video_path)
            return False
        except Exception as e:
            logger.warning("Audio detection failed for %s: %s", self.video_path, e)
            return False

    def read_frames(self) -> Iterator[tuple[int, NDArray[np.uint8]]]:
        """動画フレームを順次読み込みます。

        Yields:
            (frame_index, image_rgb): フレーム番号と RGB 画像のタプル
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
