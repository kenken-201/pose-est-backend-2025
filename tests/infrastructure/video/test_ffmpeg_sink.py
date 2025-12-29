"""FFmpegVideoSink のテスト。"""

import subprocess
from collections.abc import Generator, Iterator
from typing import cast
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from numpy.typing import NDArray

from posture_estimation.domain.exceptions import VideoProcessingError
from posture_estimation.infrastructure.video.ffmpeg_sink import FFmpegVideoSink


@pytest.fixture
def mock_subprocess() -> Generator[MagicMock, None, None]:
    """ffmpeg.run_async (subprocess.Popen) のモック。"""
    with patch("ffmpeg.output") as mock_output:
        mock_stream = MagicMock()
        mock_process = MagicMock(spec=subprocess.Popen)

        # Stdin mock
        mock_process.stdin = MagicMock()
        mock_process.poll.return_value = None
        mock_process.returncode = 0

        mock_stream.overwrite_output.return_value.run_async.return_value = mock_process
        mock_output.return_value = mock_stream

        yield mock_process


@pytest.fixture
def sample_frames_list() -> list[NDArray[np.uint8]]:
    """サンプルフレーム (2枚) のリスト。"""
    return [
        np.zeros((100, 100, 3), dtype=np.uint8),
        cast(NDArray[np.uint8], np.ones((100, 100, 3), dtype=np.uint8) * 255),
    ]


def test_save_video_success(
    mock_subprocess: MagicMock, sample_frames_list: list[NDArray[np.uint8]]
) -> None:
    """正常に動画が保存されることを確認する。"""
    sink = FFmpegVideoSink()
    # リストをイテレータとして渡す
    sink.save_video(iter(sample_frames_list), "output.mp4", 30.0)

    # 2フレーム分書き込まれたか
    assert mock_subprocess.stdin.write.call_count == 2

    # プロセスが終了されたか
    mock_subprocess.stdin.close.assert_called_once()
    mock_subprocess.wait.assert_called_once()


def test_save_video_with_audio(
    mock_subprocess: MagicMock, sample_frames_list: list[NDArray[np.uint8]]
) -> None:
    """音声付きで保存する場合の引数を確認する (ffmpeg-python のモックが難しいので簡易検証)。"""
    sink = FFmpegVideoSink()
    sink.save_video(iter(sample_frames_list), "output.mp4", 30.0, audio_path="audio.mp4")

    assert mock_subprocess.stdin.write.call_count == 2


def test_save_video_empty_frames(mock_subprocess: MagicMock) -> None:
    """空のフレーム列を渡すとエラーになることを確認する。"""
    sink = FFmpegVideoSink()
    empty_iter: Iterator[NDArray[np.uint8]] = iter([])

    with pytest.raises(VideoProcessingError, match="No frames"):
        sink.save_video(empty_iter, "output.mp4", 30.0)


def test_save_video_ffmpeg_error(
    mock_subprocess: MagicMock, sample_frames_list: list[NDArray[np.uint8]]
) -> None:
    """FFmpeg プロセスがエラー終了した場合に例外を送出することを確認する。"""
    # エラー終了をシミュレート
    mock_subprocess.returncode = 1

    sink = FFmpegVideoSink()

    with pytest.raises(VideoProcessingError, match="FFmpeg failed"):
        sink.save_video(iter(sample_frames_list), "output.mp4", 30.0)
