from unittest.mock import MagicMock, call

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
    sink.__enter__.return_value = sink

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
def mock_audio_merger() -> MagicMock:
    """音声結合サービスのモック。"""
    return MagicMock()


@pytest.fixture
def use_case(
    mock_pose_estimator: MagicMock,
    mock_storage_service: MagicMock,
    mock_temp_manager: MagicMock,
    mock_video_source_factory: MagicMock,
    mock_video_sink_factory: MagicMock,
    mock_audio_merger: MagicMock,
) -> ProcessVideoUseCase:
    """ProcessVideoUseCase フィクスチャ。"""
    return ProcessVideoUseCase(
        pose_estimator=mock_pose_estimator,
        storage_service=mock_storage_service,
        temp_manager=mock_temp_manager,
        video_source_factory=mock_video_source_factory,
        video_sink_factory=mock_video_sink_factory,
        audio_merger=mock_audio_merger,
    )


def test_execute_normal_flow(
    use_case: ProcessVideoUseCase,
    mock_video_source: MagicMock,
    mock_video_sink: MagicMock,
    mock_pose_estimator: MagicMock,
    mock_temp_manager: MagicMock,
    mock_audio_merger: MagicMock,
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
    mock_temp_manager.create_temp_path.side_effect = [
        "temp_no_audio.mp4",  # 1回目: 映像のみ
        "temp_with_audio.mp4",  # 2回目: 音声結合後
    ]

    # Frames setup (2 frames)
    import numpy as np

    frame1 = np.zeros((720, 1280, 3), dtype=np.uint8)
    frame2 = np.zeros((720, 1280, 3), dtype=np.uint8)
    mock_video_source.read_frames.return_value = iter([(0, frame1), (1, frame2)])

    # Pose estimation setup
    pose = MagicMock(spec=Pose)
    pose.keypoints = []  # 空のリストでよい(描画ループは回らない)
    mock_pose_estimator.estimate.return_value = [pose]

    # Storage setup
    mock_storage_service.upload.return_value = "output.mp4"
    mock_storage_service.generate_signed_url.return_value = "http://signed-url.com"

    # Execute
    result = use_case.execute(input_data)

    # Verify
    # 1. Video Source creation and usage
    assert mock_video_source.read_frames.called
    assert mock_video_source.get_meta.called

    # 2. Pose Estimation called for each frame
    assert mock_pose_estimator.estimate.call_count == 2

    # 3. Video Sink usage
    mock_video_sink.save_video.assert_called_once()
    _, kwargs = mock_video_sink.save_video.call_args
    assert kwargs["output_path"] == "temp_no_audio.mp4"
    assert kwargs["fps"] == 30.0

    # 4. Audio Merge
    mock_audio_merger.merge_audio.assert_called_once_with(
        video_no_audio="temp_no_audio.mp4",
        original_video="input.mp4",
        output="temp_with_audio.mp4",
    )

    # 5. Cleanup (intermediate file)
    mock_temp_manager.cleanup.assert_called()
    assert call("temp_no_audio.mp4") in mock_temp_manager.cleanup.call_args_list

    # 6. Upload
    mock_storage_service.upload.assert_called_once_with(
        "temp_with_audio.mp4", "output.mp4"
    )

    # 7. Result
    assert result.signed_url == "http://signed-url.com"
    assert result.video_meta.width == 1280
    assert result.total_poses == 2  # 2 frames * 1 pose


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
        score_threshold=0.5,
    )

    mock_temp_manager.create_temp_path.side_effect = ["temp1.mp4", "temp2.mp4"]

    # Source でエラー発生させる
    mock_video_source_factory.side_effect = VideoProcessingError("Source Error")

    # Execute & Verify
    with pytest.raises(VideoProcessingError):
        use_case.execute(input_data)

    # クリーンアップが呼ばれたか確認
    assert mock_temp_manager.cleanup.call_count == 2
    mock_temp_manager.cleanup.assert_any_call("temp1.mp4")
    mock_temp_manager.cleanup.assert_any_call("temp2.mp4")


def test_execute_storage_error(
    use_case: ProcessVideoUseCase,
    mock_video_source: MagicMock,
    mock_storage_service: MagicMock,
    mock_temp_manager: MagicMock,
) -> None:
    """ストレージエラー発生時にクリーンアップされることを検証する。"""
    from posture_estimation.application.dtos import ProcessVideoInput
    from posture_estimation.domain.exceptions import StorageError

    input_data = ProcessVideoInput(
        input_path="input.mp4",
        output_key="output.mp4",
        score_threshold=0.5,
    )
    mock_temp_manager.create_temp_path.side_effect = ["temp1.mp4", "temp2.mp4"]

    # Upload でエラー
    mock_storage_service.upload.side_effect = StorageError("Upload Failed")

    # Source mock setup requirements
    mock_video_source.read_frames.return_value = iter([]) # dummy

    with pytest.raises(StorageError):
        use_case.execute(input_data)

    assert mock_temp_manager.cleanup.call_count == 2
