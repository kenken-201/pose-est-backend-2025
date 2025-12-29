"""OpenCV を使用した動画出力。

特徴:
- 空フレームイテレータのバリデーション
- 自動的な BGR 変換
- 適切なリソース解放
"""

from collections.abc import Iterator

import cv2
import numpy as np
from numpy.typing import NDArray

from posture_estimation.domain.exceptions import VideoProcessingError
from posture_estimation.domain.interfaces import IVideoSink


class OpenCVVideoSink(IVideoSink):
    """OpenCV を使用した動画出力。"""

    def save_video(
        self, frames: Iterator[NDArray[np.uint8]], output_path: str, fps: float
    ) -> None:
        """フレーム列を動画ファイルとして保存します。

        Args:
            frames: 画像データのイテレータ (RGB 形式)
            output_path: 出力先ファイルパス
            fps: フレームレート

        Raises:
            VideoProcessingError: フレームが空または書き込み失敗時
        """
        writer = None
        frame_count = 0

        try:
            for frame_rgb in frames:
                # 最初のフレームで Writer を初期化
                if writer is None:
                    height, width, _ = frame_rgb.shape
                    fourcc = cv2.VideoWriter_fourcc(*"mp4v")  # type: ignore[attr-defined]
                    writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

                    if not writer.isOpened():
                        msg = f"Failed to create video writer: {output_path}"
                        raise VideoProcessingError(msg)

                # RGB -> BGR 変換
                frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
                writer.write(frame_bgr)
                frame_count += 1

            # 空のフレームイテレータのチェック
            if frame_count == 0:
                msg = "No frames to write: empty frame iterator provided"
                raise VideoProcessingError(msg)

        except VideoProcessingError:
            raise
        except Exception as e:
            msg = f"Error during video saving: {e}"
            raise VideoProcessingError(msg) from e
        finally:
            if writer is not None:
                writer.release()
