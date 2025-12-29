"""Dependency Injection コンテナ。"""

from dependency_injector import containers, providers

from posture_estimation.application.use_cases import ProcessVideoUseCase
from posture_estimation.infrastructure.ml.movenet_estimator import MoveNetPoseEstimator
from posture_estimation.infrastructure.storage.r2_service import R2StorageService
from posture_estimation.infrastructure.storage.temp_manager import TempFileManager
from posture_estimation.infrastructure.video.ffmpeg_sink import FFmpegVideoSink
from posture_estimation.infrastructure.video.opencv_source import OpenCVVideoSource
from posture_estimation.infrastructure.video.visualizer import OpenCVPoseVisualizer


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

    pose_visualizer = providers.Singleton(OpenCVPoseVisualizer)

    storage_service = providers.Singleton(
        R2StorageService,
        endpoint_url=config.r2.endpoint_url,
        access_key=config.r2.access_key,
        secret_key=config.r2.secret_key,
        bucket_name=config.r2.bucket_name,
    )

    temp_manager = providers.Factory(TempFileManager)

    # Factory: OpenCVVideoSource needs 'video_path' at runtime
    video_source_factory = providers.Factory(OpenCVVideoSource)

    # Factory: FFmpegVideoSink needs no args init (but used as factory in UseCase)
    video_sink_factory = providers.Factory(FFmpegVideoSink)

    # Application
    process_video_use_case = providers.Factory(
        ProcessVideoUseCase,
        pose_estimator=pose_estimator,
        pose_visualizer=pose_visualizer,
        storage_service=storage_service,
        temp_manager=temp_manager,
        video_source_factory=video_source_factory.provider,
        video_sink_factory=video_sink_factory.provider,
    )
