from collections.abc import Generator
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from posture_estimation.infrastructure.video.opencv_source import OpenCVVideoSource


@pytest.fixture
def mock_cv2() -> Generator[MagicMock, None, None]:
    """cv2.VideoCapture のモックフィクスチャ。"""
    with patch("cv2.VideoCapture") as mock:
        yield mock


def test_source_initialization(mock_cv2: MagicMock) -> None:
    """OpenCVVideoSource の初期化 (VideoCapture 作成) を確認する。"""
    source = OpenCVVideoSource("test.mp4")
    mock_cv2.assert_called_once_with("test.mp4")
    assert source.cap == mock_cv2.return_value


def test_get_meta(mock_cv2: MagicMock) -> None:
    """get_meta が動画プロパティを正しく取得してメタデータを返すか確認する。"""
    cap = mock_cv2.return_value
    # 疑似的なプロパティ設定
    import cv2

    # helper to mock get
    def mock_get(prop_id: int) -> float:
        if prop_id == cv2.CAP_PROP_FRAME_WIDTH:
            return 1280.0
        if prop_id == cv2.CAP_PROP_FRAME_HEIGHT:
            return 720.0
        if prop_id == cv2.CAP_PROP_FPS:
            return 30.0
        if prop_id == cv2.CAP_PROP_FRAME_COUNT:
            return 100.0
        return 0.0

    cap.get.side_effect = mock_get

    source = OpenCVVideoSource("test.mp4")
    meta = source.get_meta()

    assert meta.width == 1280
    assert meta.height == 720
    assert meta.fps == 30.0
    assert meta.total_frames == 100
    assert meta.duration_sec == pytest.approx(3.333, 0.001)
    # has_audio check is tricky with cv2 alone, usually assumed False or checked via ffmpeg
    # In this implementation, we might delegate audio check to ffmpeg or just default to True/False logic
    # For now, let's assume default behavior.


def test_read_frames(mock_cv2: MagicMock) -> None:
    """read_frames が正常にフレームを読み出すか確認する。"""
    cap = mock_cv2.return_value
    cap.isOpened.return_value = True

    # 2 frames then stop
    frame1 = np.zeros((720, 1280, 3), dtype=np.uint8)
    frame2 = np.zeros((720, 1280, 3), dtype=np.uint8)

    cap.read.side_effect = [(True, frame1), (True, frame2), (False, None)]

    source = OpenCVVideoSource("test.mp4")
    frames = list(source.read_frames())

    assert len(frames) == 2
    assert frames[0][0] == 0
    assert frames[1][0] == 1


def test_context_manager(mock_cv2: MagicMock) -> None:
    """Context Manager として使用した際にリソースが解放されるか確認する。"""
    cap = mock_cv2.return_value
    cap.isOpened.return_value = True

    with OpenCVVideoSource("test.mp4") as source:
        assert source.cap == cap

    # __exit__ で release が呼ばれることを確認
    cap.release.assert_called_once()
