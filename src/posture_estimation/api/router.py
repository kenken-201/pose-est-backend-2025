"""API ルーター定義。"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile

from posture_estimation.api.dependencies import (
    ProcessVideoUseCaseDep,
    TempManagerDep,
    create_video_source,
    get_max_upload_size_bytes,
)
from posture_estimation.api.exceptions import (
    MAX_VIDEO_DURATION_SEC,
    MIN_VIDEO_DURATION_SEC,
    FileTooLargeError,
    InvalidVideoFormatError,
    ModelInferenceError,
    StorageServiceUnavailableError,
    VideoTooLongError,
    VideoTooShortError,
)
from posture_estimation.api.schemas import (
    ErrorResponse,
    HealthResponse,
    ProcessVideoResponse,
    VideoMetaResponse,
)
from posture_estimation.application.dtos import ProcessVideoInput
from posture_estimation.domain.exceptions import (
    PoseEstimationError,
    StorageError,
    VideoProcessingError,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["video"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="ヘルスチェック",
    description="API の稼働状態を確認します。",
)
async def health_check() -> HealthResponse:
    """ヘルスチェックエンドポイント。"""
    return HealthResponse(status="healthy", version="1.0.0")


@router.post(
    "/process",
    response_model=ProcessVideoResponse,
    responses={
        400: {"model": ErrorResponse, "description": "無効なリクエスト"},
        413: {"model": ErrorResponse, "description": "ファイルサイズ超過"},
        422: {"model": ErrorResponse, "description": "パラメータ不正"},
        500: {"model": ErrorResponse, "description": "サーバーエラー"},
        503: {"model": ErrorResponse, "description": "サービス利用不可"},
    },
    summary="動画処理",
    description="動画をアップロードし、姿勢推定結果を含む動画を生成します。",
)
async def process_video(
    file: Annotated[UploadFile, File(description="処理対象の動画ファイル")],
    use_case: ProcessVideoUseCaseDep,
    temp_manager: TempManagerDep,
    score_threshold: Annotated[
        float,
        Form(
            description="姿勢検出の閾値 (0.0-1.0)",
            ge=0.0,
            le=1.0,
        ),
    ] = 0.2,
    max_size: Annotated[int, Depends(get_max_upload_size_bytes)] = 0,
) -> ProcessVideoResponse:
    """動画処理エンドポイント。

    Args:
        file: アップロードされた動画ファイル
        use_case: 動画処理ユースケース
        temp_manager: 一時ファイルマネージャ
        score_threshold: 姿勢検出の閾値
        max_size: 最大アップロードサイズ

    Returns:
        処理結果 (署名付き URL, メタデータ, 統計情報)
    """
    input_temp_path: str | None = None

    try:
        # 1. ファイルサイズチェック
        if file.size and file.size > max_size:
            size_mb = file.size / (1024 * 1024)
            max_mb = max_size / (1024 * 1024)
            raise FileTooLargeError(size_mb, max_mb)

        # 2. 一時ファイルに保存
        suffix = _get_file_extension(file.filename or "video.mp4")
        input_temp_path = temp_manager.create_temp_path(suffix=suffix)

        # ファイル内容を読み取り
        content = await file.read()
        from pathlib import Path
        Path(input_temp_path).write_bytes(content)

        logger.info("Saved uploaded file to %s", input_temp_path)

        # 3. 動画バリデーション
        _validate_video(input_temp_path)

        # 4. ユースケース実行
        output_key = _generate_output_key(file.filename or "video.mp4")
        input_dto = ProcessVideoInput(
            input_path=input_temp_path,
            output_key=output_key,
            score_threshold=score_threshold,
        )

        result = use_case.execute(input_dto)

        # 5. レスポンス変換
        return ProcessVideoResponse(
            signed_url=result.signed_url,
            video_meta=VideoMetaResponse(
                width=result.video_meta.width,
                height=result.video_meta.height,
                fps=result.video_meta.fps,
                duration_sec=result.video_meta.duration_sec,
                has_audio=result.video_meta.has_audio,
            ),
            total_poses=result.total_poses,
            processing_time_sec=result.processing_time_sec,
        )

    except (
        FileTooLargeError,
        InvalidVideoFormatError,
        VideoTooShortError,
        VideoTooLongError,
        ModelInferenceError,
        StorageServiceUnavailableError,
    ):
        # API 例外はそのまま再送出
        raise

    except VideoProcessingError as e:
        logger.exception("Video processing error")
        raise InvalidVideoFormatError(str(e)) from e

    except PoseEstimationError as e:
        logger.exception("Pose estimation error")
        raise ModelInferenceError(str(e)) from e

    except StorageError as e:
        logger.exception("Storage error")
        raise StorageServiceUnavailableError(str(e)) from e

    except Exception as e:
        logger.exception("Unexpected error during video processing")
        raise ModelInferenceError(f"Unexpected error: {e}") from e

    finally:
        # 入力一時ファイルのクリーンアップ
        if input_temp_path:
            temp_manager.cleanup(input_temp_path)


def _get_file_extension(filename: str) -> str:
    """ファイル名から拡張子を取得します。"""
    if "." in filename:
        return "." + filename.rsplit(".", 1)[-1]
    return ".mp4"


def _generate_output_key(original_filename: str) -> str:
    """出力ファイルのキーを生成します。"""
    import uuid

    base_name = original_filename.rsplit(".", 1)[0] if "." in original_filename else original_filename
    unique_id = uuid.uuid4().hex[:8]
    return f"processed/{base_name}_{unique_id}.mp4"


def _validate_video(video_path: str) -> None:
    """動画ファイルをバリデーションします。

    Args:
        video_path: 動画ファイルパス

    Raises:
        InvalidVideoFormatError: 読み込めない場合
        VideoTooShortError: 動画が短すぎる場合
        VideoTooLongError: 動画が長すぎる場合
    """
    try:
        with create_video_source(video_path) as source:
            meta = source.get_meta()

            if meta.duration_sec < MIN_VIDEO_DURATION_SEC:
                raise VideoTooShortError(meta.duration_sec)

            if meta.duration_sec > MAX_VIDEO_DURATION_SEC:
                raise VideoTooLongError(meta.duration_sec)

    except (VideoTooShortError, VideoTooLongError):
        raise
    except Exception as e:
        raise InvalidVideoFormatError(f"Cannot read video: {e}") from e

