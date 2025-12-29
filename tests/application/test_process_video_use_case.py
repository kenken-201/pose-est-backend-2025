from unittest.mock import MagicMock

import pytest

from posture_estimation.application.dtos import ProcessVideoInput
from posture_estimation.application.use_cases import ProcessVideoUseCase
from posture_estimation.domain.entities import Pose
from posture_estimation.domain.values import VideoMeta


@pytest.fixture
def mock_pose_estimator() -> MagicMock:
    """姿勢推定エンジンのモック。"""
    return MagicMock()


@pytest.fixture
def mock_pose_visualizer() -> MagicMock:
    """姿勢描画サービスのモック。"""
    return MagicMock()


@pytest.fixture
def mock_storage_service() -> MagicMock:
    """ストレージサービスのモック。"""
    return MagicMock()


@pytest.fixture
def mock_temp_manager() -> MagicMock:
    """一時ファイル管理のモック。"""
    return MagicMock()


@pytest.fixture
def mock_video_source() -> MagicMock:
    """動画ソースのモック。"""
    source = MagicMock()
    # デフォルトのメタデータ
    source.get_meta.return_value = VideoMeta(
        width=1280,
        height=720,
        fps=30.0,
        total_frames=100,
        duration_sec=3.33,
        has_audio=True,
    )
    # デフォルトで空のフレーム列を返す (無限ループ防止)
    source.read_frames.return_value = iter([])
    source.__enter__.return_value = source
    return source


@pytest.fixture
def mock_video_source_factory(mock_video_source: MagicMock) -> MagicMock:
    """動画ソース生成ファクトリのモック。"""
    factory = MagicMock()
    factory.return_value = mock_video_source
    return factory


@pytest.fixture
def mock_video_sink() -> MagicMock:
    """動画シンクのモック。"""
    sink = MagicMock()

    def consume_frames(*args: object, **kwargs: object) -> None:
        # イテレータを消費して、中の処理を実行させる
        frames = kwargs.get("frames")
        if frames is None and args:
            frames = args[0]
        if frames:
            list(frames)  # type: ignore

    sink.save_video.side_effect = consume_frames
    return sink


@pytest.fixture
def mock_video_sink_factory(mock_video_sink: MagicMock) -> MagicMock:
    """動画シンク生成ファクトリのモック。"""
    factory = MagicMock()
    factory.return_value = mock_video_sink
    return factory


@pytest.fixture
def use_case(
    mock_pose_estimator: MagicMock,
    mock_pose_visualizer: MagicMock,
    mock_storage_service: MagicMock,
    mock_temp_manager: MagicMock,
    mock_video_source_factory: MagicMock,
    mock_video_sink_factory: MagicMock,
) -> ProcessVideoUseCase:
    """ProcessVideoUseCase フィクスチャ。"""
    return ProcessVideoUseCase(
        pose_estimator=mock_pose_estimator,
        pose_visualizer=mock_pose_visualizer,
        storage_service=mock_storage_service,
        temp_manager=mock_temp_manager,
        video_source_factory=mock_video_source_factory,
        video_sink_factory=mock_video_sink_factory,
    )


def test_execute_normal_flow(
    use_case: ProcessVideoUseCase,
    mock_video_source: MagicMock,
    mock_video_sink: MagicMock,
    mock_pose_estimator: MagicMock,
    mock_pose_visualizer: MagicMock,
    mock_temp_manager: MagicMock,
    mock_storage_service: MagicMock,
) -> None:
    """正常系の処理フローを検証する。"""
    # Setup
    input_data = ProcessVideoInput(
        input_path="input.mp4",
        output_key="output.mp4",
        score_threshold=0.5,
    )

    # Temp paths
    mock_temp_manager.create_temp_path.return_value = "temp_output.mp4"

    # Frames setup (2 frames)
    import numpy as np

    frame1 = np.zeros((720, 1280, 3), dtype=np.uint8)
    frame2 = np.zeros((720, 1280, 3), dtype=np.uint8)
    mock_video_source.read_frames.return_value = iter([(0, frame1), (1, frame2)])

    # Pose estimation setup
    pose = MagicMock(spec=Pose)
    pose.keypoints = []
    mock_pose_estimator.estimate.return_value = [pose]

    # Storage setup
    mock_storage_service.upload.return_value = "output.mp4"
    mock_storage_service.generate_signed_url.return_value = "http://signed-url.com"

    # Execute
    result = use_case.execute(input_data)

    # Verify
    # 1. Video Source usage
    assert mock_video_source.read_frames.called
    assert mock_video_source.get_meta.called

    # 2. Pose Estimation & Visualization called for each frame
    assert mock_pose_estimator.estimate.call_count == 2
    assert mock_pose_visualizer.draw.call_count == 2
    mock_pose_visualizer.draw.assert_called_with(frame2, [pose])

    # 3. Video Sink usage (with audio path)
    mock_video_sink.save_video.assert_called_once()
    _, kwargs = mock_video_sink.save_video.call_args
    assert kwargs["output_path"] == "temp_output.mp4"
    assert kwargs["fps"] == 30.0
    assert kwargs["audio_path"] == "input.mp4"

    # 4. Cleanup
    mock_temp_manager.cleanup.assert_called_once_with("temp_output.mp4")

    # 5. Upload
    mock_storage_service.upload.assert_called_once_with(
        "temp_output.mp4", "output.mp4"
    )

    # 6. Result
    assert result.signed_url == "http://signed-url.com"
    assert result.video_meta.width == 1280
    assert result.total_poses == 2  # 2 frames * 1 pose


def test_execute_no_audio_flow(
    use_case: ProcessVideoUseCase,
    mock_video_source: MagicMock,
    mock_video_sink: MagicMock,
    mock_temp_manager: MagicMock,
) -> None:
    """音声なし動画の処理フローを検証する。"""
    # Setup
    input_data = ProcessVideoInput(
        input_path="input_silent.mp4",
        output_key="output.mp4",
    )
    mock_temp_manager.create_temp_path.return_value = "temp_output.mp4"

    # Metadata (no audio)
    mock_video_source.get_meta.return_value = VideoMeta(
        width=1280,
        height=720,
        fps=30.0,
        total_frames=10,
        duration_sec=1.0,
        has_audio=False,
    )
    # Dummy frames
    mock_video_source.read_frames.return_value = iter([])

    # Execute
    use_case.execute(input_data)

    # Verify sink call
    _, kwargs = mock_video_sink.save_video.call_args
    assert kwargs["audio_path"] is None


def test_execute_cleanup_on_error(
    use_case: ProcessVideoUseCase,
    mock_video_source_factory: MagicMock,
    mock_temp_manager: MagicMock,
) -> None:
    """エラー発生時に一時ファイルがクリーンアップされることを検証する。"""
    from posture_estimation.application.dtos import ProcessVideoInput
    from posture_estimation.domain.exceptions import VideoProcessingError

    # Setup
    input_data = ProcessVideoInput(
        input_path="input.mp4",
        output_key="output.mp4",
    )
    mock_temp_manager.create_temp_path.return_value = "temp_error.mp4"

    # Source error
    mock_video_source_factory.side_effect = VideoProcessingError("Source Error")

    # Execute & Verify
    with pytest.raises(VideoProcessingError):
        use_case.execute(input_data)

    assert mock_temp_manager.cleanup.called
    mock_temp_manager.cleanup.assert_called_with("temp_error.mp4")
