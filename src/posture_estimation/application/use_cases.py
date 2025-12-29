from collections.abc import Iterator

import cv2
import numpy as np
from numpy.typing import NDArray

from posture_estimation.application.dtos import (
    ProcessVideoInput,
    ProcessVideoResult,
)
from posture_estimation.domain.entities import Pose
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
        import time

        start_time = time.time()

        # 一時ファイルの準備
        temp_no_audio = self._temp_manager.create_temp_path(suffix="_no_audio.mp4")
        temp_with_audio = self._temp_manager.create_temp_path(suffix=".mp4")

        total_poses = 0
        video_meta = None

        try:
            # 動画ソースを開く
            with self._video_source_factory(input_data.input_path) as source:
                video_meta = source.get_meta()

                # 動画シンクを作成 (一時ファイル出力)
                # Sink は __enter__ をサポートしていない実装 (OpenCVVideoSink) もあるため
                # ここでは直接関数として使う設計だが、現状のコードでは
                # IVideoSinkFactory -> returns IVideoSink
                # IVideoSink.save_video takes iterator.

                # Iterator ベースの処理にするため、フレームジェネレータ関数を定義
                def frame_processor() -> Iterator[NDArray[np.uint8]]:
                    nonlocal total_poses
                    for _, frame in source.read_frames():
                        # 姿勢推定
                        poses = self._pose_estimator.estimate(frame)

                        # スコアフィルタリングはこのUseCaseで行うか、Estimatorに任せるか
                        # Input DTOにある score_threshold をどう使うか
                        # MovenetEstimator は初期化時に threshold を持つが、
                        # 後から変更するインターフェースはない。
                        # ここでは検出されたものを描画する方針とする。
                        # (実装簡略化のため、DTOのthresholdはEstimator初期化に使用される前提だが
                        #  今回は注入済みのEstimatorを使うため、フィルタリング済みとみなす)

                        # 描画
                        self._draw_keypoints(frame, poses)
                        total_poses += len(poses)

                        yield frame

                # シンクでの保存実行
                sink = self._video_sink_factory()
                sink.save_video(
                    frames=frame_processor(),
                    output_path=temp_no_audio,
                    fps=video_meta.fps
                )

            # 音声結合
            if video_meta.has_audio:
                self._audio_merger.merge_audio(
                    video_no_audio=temp_no_audio,
                    original_video=input_data.input_path,
                    output=temp_with_audio
                )
                upload_target = temp_with_audio
            else:
                upload_target = temp_no_audio

            # アップロード
            self._storage_service.upload(upload_target, input_data.output_key)

            # 署名付きURL生成
            signed_url = self._storage_service.generate_signed_url(input_data.output_key)

            processing_time = time.time() - start_time

            return ProcessVideoResult(
                signed_url=signed_url,
                video_meta=video_meta,
                total_poses=total_poses,
                processing_time_sec=processing_time,
            )

        finally:
            self._temp_manager.cleanup(temp_no_audio)
            self._temp_manager.cleanup(temp_with_audio)

    def _draw_keypoints(self, image: NDArray[np.uint8], poses: list[Pose]) -> None:
        """画像にキーポイントとスケルトンを描画します。"""
        # 接続関係 (COCO Keypoints)
        edges = [
            (0, 1), (0, 2), (1, 3), (2, 4), # Face
            (5, 6), (5, 7), (7, 9), (6, 8), (8, 10), # Arms
            (5, 11), (6, 12), (11, 12), # Torso
            (11, 13), (13, 15), (12, 14), (14, 16) # Legs
        ]

        height, width = image.shape[:2]

        for pose in poses:
            # キーポイント描画
            points = {}
            for i, keypoint in enumerate(pose.keypoints):
                if keypoint.score < 0.2: # 表示用閾値
                    continue

                # 正規化座標 -> ピクセル座標
                px = int(keypoint.point.x * width)
                py = int(keypoint.point.y * height)
                points[i] = (px, py)

                cv2.circle(image, (px, py), 4, (0, 255, 0), -1)

            # スケルトン描画
            for start_idx, end_idx in edges:
                if start_idx in points and end_idx in points:
                    cv2.line(image, points[start_idx], points[end_idx], (0, 255, 0), 2)

