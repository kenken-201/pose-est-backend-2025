"""Dependency Injection コンテナ。"""

from dependency_injector import containers, providers

from posture_estimation.application.use_cases import ProcessVideoUseCase
from posture_estimation.infrastructure.ml.movenet_estimator import MoveNetPoseEstimator
from posture_estimation.infrastructure.storage.r2_service import R2StorageService
from posture_estimation.infrastructure.storage.temp_manager import TempFileManager
from posture_estimation.infrastructure.video.ffmpeg_merger import FFmpegAudioMerger
from posture_estimation.infrastructure.video.opencv_sink import OpenCVVideoSink
from posture_estimation.infrastructure.video.opencv_source import OpenCVVideoSource


class AppContainer(containers.DeclarativeContainer):
    """アプリケーション全体の DI コンテナ。"""

    config = providers.Configuration()

    # Infrastructure
    pose_estimator = providers.Singleton(
        MoveNetPoseEstimator,
        model_url=config.ml.model_url,
        score_threshold=config.ml.score_threshold,
        target_size=config.ml.target_size,
    )

    storage_service = providers.Singleton(
        R2StorageService,
        endpoint_url=config.r2.endpoint_url,
        access_key=config.r2.access_key,
        secret_key=config.r2.secret_key,
        bucket_name=config.r2.bucket_name,
    )

    temp_manager = providers.Factory(TempFileManager)

    audio_merger = providers.Factory(FFmpegAudioMerger)

    # Factory: OpenCVVideoSource needs 'video_path' at runtime
    video_source_factory = providers.Factory(OpenCVVideoSource)

    # Factory: OpenCVVideoSink needs no args init (but used as factory in UseCase)
    video_sink_factory = providers.Factory(OpenCVVideoSink)

    # Application
    process_video_use_case = providers.Factory(
        ProcessVideoUseCase,
        pose_estimator=pose_estimator,
        storage_service=storage_service,
        temp_manager=temp_manager,
        video_source_factory=video_source_factory.provider,
        video_sink_factory=video_sink_factory.provider,
        audio_merger=audio_merger,
    )
