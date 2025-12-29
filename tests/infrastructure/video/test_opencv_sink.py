
from collections.abc import Generator
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from posture_estimation.infrastructure.video.opencv_sink import OpenCVVideoSink


@pytest.fixture
def mock_cv2_writer() -> Generator[MagicMock, None, None]:
    """cv2.VideoWriter のモックフィクスチャ。"""
    with patch("cv2.VideoWriter") as mock:
        yield mock


def test_save_video(mock_cv2_writer: MagicMock) -> None:
    """save_video が正常に Writer を初期化し書き込むか確認する。"""
    sink = OpenCVVideoSink()

    frames = [
        np.zeros((100, 100, 3), dtype=np.uint8),
        np.zeros((100, 100, 3), dtype=np.uint8)
    ]

    sink.save_video(iter(frames), "output.mp4", fps=30.0)

    # Writer initialization check
    import cv2
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")  # type: ignore
    mock_cv2_writer.assert_called_once_with("output.mp4", fourcc, 30.0, (100, 100))

    # Write calls check
    writer_instance = mock_cv2_writer.return_value
    assert writer_instance.write.call_count == 2
    writer_instance.release.assert_called_once()


def test_save_video_empty_frames(mock_cv2_writer: MagicMock) -> None:
    """空のフレームイテレータでエラーが発生することを確認する。"""
    from posture_estimation.domain.exceptions import VideoProcessingError

    sink = OpenCVVideoSink()

    with pytest.raises(VideoProcessingError, match="No frames to write"):
        sink.save_video(iter([]), "output.mp4", fps=30.0)
