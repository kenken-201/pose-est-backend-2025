"""FFmpeg を使用した動画出力。

特徴:
- Stdin パイプラインによる低遅延・低 I/O 処理
- 映像と音声のリアルタイム結合
- libx264 による高効率エンコード
"""

import logging
import subprocess
from collections.abc import Iterator

import ffmpeg  # type: ignore[import-untyped]
import numpy as np
from numpy.typing import NDArray

from posture_estimation.domain.exceptions import VideoProcessingError
from posture_estimation.domain.interfaces import IVideoSink

logger = logging.getLogger(__name__)


class FFmpegVideoSink(IVideoSink):
    """FFmpeg を使用した動画出力。

    OpenCV を介さず、FFmpeg プロセスへ直接フレームをパイプ入力することで
    中間ファイルの生成を回避し、音声結合も同時に行います。
    """

    def save_video(
        self,
        frames: Iterator[NDArray[np.uint8]],
        output_path: str,
        fps: float,
        audio_path: str | None = None,
    ) -> None:
        """フレーム列を動画ファイルとして保存します。

        Args:
            frames: 画像データのイテレータ (RGB 形式)
            output_path: 出力先ファイルパス
            fps: フレームレート
            audio_path: 音声ソースとなる動画/音声ファイルのパス

        Raises:
            VideoProcessingError: FFmpeg 実行失敗時
        """
        logger.debug(
            "Starting video save: output=%s, fps=%s, audio=%s",
            output_path, fps, audio_path
        )
        process: subprocess.Popen[bytes] | None = None

        try:
            # フレームを消費してプロセスに書き込む
            process = self._write_frames(frames, output_path, fps, audio_path)

            if process:
                if process.stdin:
                    process.stdin.close()
                process.wait()

                if process.returncode != 0:
                    msg = f"FFmpeg failed with return code {process.returncode}"
                    logger.error(msg)
                    raise VideoProcessingError(msg)

            logger.info("Video saved successfully: %s", output_path)

        except VideoProcessingError:
            raise
        except Exception as e:
            msg = f"Error during video saving with FFmpeg: {e}"
            logger.exception(msg)
            raise VideoProcessingError(msg) from e
        finally:
            if process and process.poll() is None:
                logger.warning("Killing orphaned FFmpeg process")
                process.kill()

    def _write_frames(
        self,
        frames: Iterator[NDArray[np.uint8]],
        output_path: str,
        fps: float,
        audio_path: str | None,
    ) -> subprocess.Popen[bytes] | None:
        """フレームをイテレートし、FFmpeg プロセスに書き込みます。

        Args:
            frames: フレームイテレータ
            output_path: 出力先
            fps: フレームレート
            audio_path: 音声パス

        Returns:
            使用した FFmpeg プロセス (フレームが空の場合は None)

        Raises:
            VideoProcessingError: フレームが空の場合
        """
        process: subprocess.Popen[bytes] | None = None
        first_frame = True

        for frame_rgb in frames:
            if first_frame:
                height, width, _ = frame_rgb.shape
                process = self._setup_ffmpeg_process(
                    output_path, width, height, fps, audio_path
                )
                first_frame = False

            if process and process.stdin:
                # RGB -> Raw bytes
                process.stdin.write(frame_rgb.tobytes())

        if first_frame:
            msg = "No frames to write: empty frame iterator provided"
            logger.error(msg)
            raise VideoProcessingError(msg)

        logger.debug("Wrote frames to FFmpeg process")

        return process

    def _setup_ffmpeg_process(
        self,
        output_path: str,
        width: int,
        height: int,
        fps: float,
        audio_path: str | None = None,
    ) -> subprocess.Popen[bytes]:
        """FFmpeg プロセスをセットアップ。

        Args:
            output_path: 出力先
            width: 幅
            height: 高さ
            fps: フレームレート
            audio_path: 音声ソース (任意)

        Returns:
            Popen プロセスオブジェクト
        """
        # 映像入力 (Stdin Pipe)
        video_input = ffmpeg.input(
            "pipe:",
            format="rawvideo",
            pix_fmt="rgb24",
            s=f"{width}x{height}",
            r=fps,
        )

        inputs = [video_input]

        # 音声入力 (あれば)
        if audio_path:
            audio_input = ffmpeg.input(audio_path).audio
            inputs.append(audio_input)

        # 出力設定
        # - vcodec: libx264 (H.264)
        # - acodec: aac (音声がある場合)
        # - pix_fmt: yuv420p (多くのプレイヤーとの互換性)
        output_args = {
            "vcodec": "libx264",
            "pix_fmt": "yuv420p",
            "crf": 23,  # 標準的な画質/ファイルサイズバランス
            "preset": "medium",
        }

        if audio_path:
            output_args["acodec"] = "aac"
            output_args["shortest"] = None  # 映像・音声の短い方に合わせる

        stream = ffmpeg.output(
            *inputs,
            output_path,
            **output_args
        ).overwrite_output()

        # ffmpeg-python の型定義が不完全なためキャスト
        from typing import cast

        return cast(subprocess.Popen[bytes], stream.run_async(pipe_stdin=True, quiet=True))
