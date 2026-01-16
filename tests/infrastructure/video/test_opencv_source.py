import json
import subprocess
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


@pytest.fixture
def mock_subprocess_run() -> Generator[MagicMock, None, None]:
    """subprocess.run のモックフィクスチャ。"""
    with patch(
        "posture_estimation.infrastructure.video.opencv_source.subprocess.run"
    ) as mock:
        yield mock


def test_source_initialization(mock_cv2: MagicMock) -> None:
    """OpenCVVideoSource の初期化 (VideoCapture 作成) を確認する。"""
    source = OpenCVVideoSource("test.mp4")
    mock_cv2.assert_called_once_with("test.mp4")
    assert source.cap == mock_cv2.return_value


def test_get_meta_with_audio(
    mock_cv2: MagicMock, mock_subprocess_run: MagicMock
) -> None:
    """get_meta が動画プロパティを正しく取得 (音声あり) を確認する。"""
    cap = mock_cv2.return_value
    import cv2

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

    # ffprobe が音声ストリームを返す
    mock_subprocess_run.return_value = MagicMock(
        returncode=0,
        stdout=json.dumps({"streams": [{"codec_type": "audio"}]}),
    )

    source = OpenCVVideoSource("test.mp4")
    meta = source.get_meta()

    assert meta.width == 1280
    assert meta.height == 720
    assert meta.fps == 30.0
    assert meta.total_frames == 100
    assert meta.duration_sec == pytest.approx(3.333, 0.001)
    assert meta.has_audio is True


def test_get_meta_without_audio(
    mock_cv2: MagicMock, mock_subprocess_run: MagicMock
) -> None:
    """get_meta が動画プロパティを正しく取得 (音声なし) を確認する。"""
    cap = mock_cv2.return_value
    import cv2

    def mock_get(prop_id: int) -> float:
        if prop_id == cv2.CAP_PROP_FRAME_WIDTH:
            return 1920.0
        if prop_id == cv2.CAP_PROP_FRAME_HEIGHT:
            return 1080.0
        if prop_id == cv2.CAP_PROP_FPS:
            return 60.0
        if prop_id == cv2.CAP_PROP_FRAME_COUNT:
            return 600.0
        return 0.0

    cap.get.side_effect = mock_get

    # ffprobe が空のストリームを返す
    mock_subprocess_run.return_value = MagicMock(
        returncode=0,
        stdout=json.dumps({"streams": []}),
    )

    source = OpenCVVideoSource("test.mp4")
    meta = source.get_meta()

    assert meta.has_audio is False


def test_detect_audio_ffprobe_not_found(mock_cv2: MagicMock) -> None:
    """FFprobe が見つからない場合は False を返す。"""
    source = OpenCVVideoSource("test.mp4")

    with patch(
        "posture_estimation.infrastructure.video.opencv_source.subprocess.run",
        side_effect=FileNotFoundError(),
    ):
        assert source._detect_audio() is False


def test_detect_audio_ffprobe_timeout(mock_cv2: MagicMock) -> None:
    """FFprobe がタイムアウトした場合は False を返す。"""
    source = OpenCVVideoSource("test.mp4")

    with patch(
        "posture_estimation.infrastructure.video.opencv_source.subprocess.run",
        side_effect=subprocess.TimeoutExpired("ffprobe", 10),
    ):
        assert source._detect_audio() is False


def test_detect_audio_invalid_json(
    mock_cv2: MagicMock, mock_subprocess_run: MagicMock
) -> None:
    """FFprobe が無効な JSON を返した場合は False を返す。"""
    mock_subprocess_run.return_value = MagicMock(
        returncode=0,
        stdout="invalid json",
    )

    source = OpenCVVideoSource("test.mp4")
    assert source._detect_audio() is False


def test_read_frames(mock_cv2: MagicMock) -> None:
    """read_frames が正常にフレームを読み出すか確認する。"""
    cap = mock_cv2.return_value
    cap.isOpened.return_value = True

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

    cap.release.assert_called_once()
