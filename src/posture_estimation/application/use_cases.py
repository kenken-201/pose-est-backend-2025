from posture_estimation.application.dtos import (
    ProcessVideoInput,
    ProcessVideoResult,
)
from posture_estimation.domain.interfaces import (
    IAudioMerger,
    IPoseEstimator,
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
        storage_service: IStorageService,
        temp_manager: ITempManager,
        video_source_factory: IVideoSourceFactory,
        video_sink_factory: IVideoSinkFactory,
        audio_merger: IAudioMerger,
    ) -> None:
        """初期化。

        Args:
            pose_estimator: 姿勢推定サービス
            storage_service: ストレージサービス
            temp_manager: 一時ファイル管理
            video_source_factory: 動画ソース生成ファクトリ
            video_sink_factory: 動画シンク生成ファクトリ
            audio_merger: 音声結合サービス
        """
        self._pose_estimator = pose_estimator
        self._storage_service = storage_service
        self._temp_manager = temp_manager
        self._video_source_factory = video_source_factory
        self._video_sink_factory = video_sink_factory
        self._audio_merger = audio_merger

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
        # Phase 4-2 で実装
        raise NotImplementedError
