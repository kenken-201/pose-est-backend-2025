from collections.abc import Generator
from unittest.mock import MagicMock, patch

import pytest

from posture_estimation.domain.exceptions import VideoProcessingError
from posture_estimation.infrastructure.video.ffmpeg_merger import FFmpegAudioMerger


@pytest.fixture
def mock_ffmpeg() -> Generator[tuple[MagicMock, MagicMock], None, None]:
    """ffmpeg-python のモックフィクスチャ。"""
    with patch("ffmpeg.input") as mock_input, \
         patch("ffmpeg.output") as mock_output:
        yield (mock_input, mock_output)

def test_merge_audio(mock_ffmpeg: tuple[MagicMock, MagicMock]) -> None:
    """merge_audio が正常に ffmpeg コマンドを構築するか確認する。"""
    mock_input, mock_output = mock_ffmpeg
    merger = FFmpegAudioMerger()

    # Setup mock chain
    input_video = MagicMock()
    input_audio = MagicMock()
    mock_input.side_effect = [input_video, input_audio] # video_no_audio, original_video

    output_obj = MagicMock()
    mock_output.return_value = output_obj

    merger.merge_audio("processed.mp4", "original.mp4", "final.mp4")

    # Verify input calls
    # 1. video input (processed.mp4)
    # 2. audio input (original.mp4)
    assert mock_input.call_count == 2
    mock_input.assert_any_call("processed.mp4")
    mock_input.assert_any_call("original.mp4")

    # Verify output call
    # output(input_video, input_audio.audio, "final.mp4", vcodec="copy", acodec="aac")
    mock_output.assert_called_once()
    args, kwargs = mock_output.call_args
    assert args[2] == "final.mp4"
    assert kwargs["vcodec"] == "copy"
    assert kwargs["acodec"] == "aac"

    # Verify run
    output_obj.run.assert_called_once_with(overwrite_output=True, capture_stdout=True, capture_stderr=True)

def test_merge_audio_error(mock_ffmpeg: tuple[MagicMock, MagicMock]) -> None:
    """Ffmpeg 実行エラー時に VideoProcessingError を送出するか確認する。"""
    _, mock_output = mock_ffmpeg
    merger = FFmpegAudioMerger()

    mock_output.return_value.run.side_effect = Exception("ffmpeg error")

    with pytest.raises(VideoProcessingError, match="Audio merge failed"):
        merger.merge_audio("processed.mp4", "original.mp4", "final.mp4")
