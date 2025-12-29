from collections.abc import Iterator

import numpy as np
from numpy.typing import NDArray

from posture_estimation.application.dtos import (
    ProcessVideoInput,
    ProcessVideoResult,
)
from posture_estimation.domain.interfaces import (
    IPoseEstimator,
    IPoseVisualizer,
    IStorageService,
    ITempManager,
    IVideoSinkFactory,
    IVideoSourceFactory,
)


class ProcessVideoUseCase:
    """動画の姿勢推定処理を行うユースケース。"""

    def __init__(
        self,
        pose_estimator: IPoseEstimator,
        pose_visualizer: IPoseVisualizer,
        storage_service: IStorageService,
        temp_manager: ITempManager,
        video_source_factory: IVideoSourceFactory,
        video_sink_factory: IVideoSinkFactory,
    ) -> None:
        """初期化。

        Args:
            pose_estimator: 姿勢推定サービス
            pose_visualizer: 姿勢描画サービス
            storage_service: ストレージサービス
            temp_manager: 一時ファイル管理
            video_source_factory: 動画ソース生成ファクトリ
            video_sink_factory: 動画シンク生成ファクトリ
        """
        self._pose_estimator = pose_estimator
        self._pose_visualizer = pose_visualizer
        self._storage_service = storage_service
        self._temp_manager = temp_manager
        self._video_source_factory = video_source_factory
        self._video_sink_factory = video_sink_factory

    def execute(self, input_data: ProcessVideoInput) -> ProcessVideoResult:
        """動画処理を実行します。

        Args:
            input_data: 処理入力パラメータ

        Returns:
            処理結果 (署名付きURLなど)

        Raises:
            VideoProcessingError: 動画処理に失敗した場合
            PoseEstimationError: 姿勢推定に失敗した場合
            StorageError: 保存に失敗した場合
        """
        import time

        start_time = time.time()

        # 一時ファイルの準備
        temp_output = self._temp_manager.create_temp_path(suffix=".mp4")

        total_poses = 0
        video_meta = None

        try:
            # 動画ソースを開く
            with self._video_source_factory(input_data.input_path) as source:
                video_meta = source.get_meta()

                # フレーム処理ジェネレータ
                def frame_processor() -> Iterator[NDArray[np.uint8]]:
                    nonlocal total_poses
                    for _, frame in source.read_frames():
                        # 姿勢推定
                        poses = self._pose_estimator.estimate(frame)

                        # 描画 (Visualizer に委譲)
                        self._pose_visualizer.draw(frame, poses)
                        total_poses += len(poses)

                        yield frame

                # シンクでの保存実行 (音声パスを渡して内部で結合)
                sink = self._video_sink_factory()
                sink.save_video(
                    frames=frame_processor(),
                    output_path=temp_output,
                    fps=video_meta.fps,
                    audio_path=input_data.input_path if video_meta.has_audio else None,
                )

            # アップロード
            self._storage_service.upload(temp_output, input_data.output_key)

            # 署名付きURL生成
            signed_url = self._storage_service.generate_signed_url(
                input_data.output_key
            )

            processing_time = time.time() - start_time

            return ProcessVideoResult(
                signed_url=signed_url,
                video_meta=video_meta,
                total_poses=total_poses,
                processing_time_sec=processing_time,
            )

        finally:
            self._temp_manager.cleanup(temp_output)

