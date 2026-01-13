"""API ルーター定義。"""

import logging
import shutil
import uuid
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile

from posture_estimation.api.dependencies import (
    ProcessVideoUseCaseDep,
    TempManagerDep,
    get_max_upload_size_bytes,
)
from posture_estimation.api.exceptions import (
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
from posture_estimation.application.use_cases import (
    MIN_VIDEO_DURATION_SEC,
)
from posture_estimation.domain.exceptions import (
    PoseEstimationError,
    StorageError,
    VideoDurationError,
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
def health_check() -> HealthResponse:
    """ヘルスチェックエンドポイント。"""
    return HealthResponse(status="healthy", version="1.0.0")


@router.post(
    "/process",
    response_model=ProcessVideoResponse,
    summary="動画処理",
    description="""
    アップロードされた動画に対して姿勢推定を行い、結果を返します。

    ## 制約事項

    - **動画時間**: 3.0秒以上、420.0秒 (7分) 以内
    - **ファイルサイズ**: 100MB 以下
    - **フォーマット**: 一般的な動画フォーマット (MP4, MOV, AVI 等)
    - **音声**: 音声トラックが含まれる場合、出力動画にも保持されます
    """,
    responses={
        400: {
            "model": ErrorResponse,
            "description": "無効なリクエスト (動画時間外、フォーマット不正)",
            "content": {
                "application/json": {
                    "examples": {
                        "VIDEO_TOO_SHORT": {
                            "summary": "動画が短すぎる",
                            "value": {
                                "error": {
                                    "code": "VIDEO_TOO_SHORT",
                                    "message": "Video duration 1.5s is too short (min: 3.0s)",
                                }
                            },
                        },
                        "VIDEO_TOO_LONG": {
                            "summary": "動画が長すぎる",
                            "value": {
                                "error": {
                                    "code": "VIDEO_TOO_LONG",
                                    "message": "Video duration 500.0s is too long (max: 420.0s)",
                                }
                            },
                        },
                        "INVALID_VIDEO_FORMAT": {
                            "summary": "無効なフォーマット",
                            "value": {
                                "error": {
                                    "code": "INVALID_VIDEO_FORMAT",
                                    "message": "Unable to read video file",
                                }
                            },
                        },
                    }
                }
            },
        },
        413: {
            "model": ErrorResponse,
            "description": "ファイルサイズ超過 (Max: 100MB)",
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "code": "FILE_TOO_LARGE",
                            "message": "File size 150MB exceeds limit of 100MB",
                        }
                    }
                }
            },
        },
        422: {
            "model": ErrorResponse,
            "description": "パラメータ不正 (閾値範囲外など)",
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "code": "INVALID_PARAMETER",
                            "message": "Score threshold must be between 0.0 and 1.0",
                        }
                    }
                }
            },
        },
        500: {
            "model": ErrorResponse,
            "description": "サーバー内部エラー (推論失敗など)",
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "code": "MODEL_INFERENCE_ERROR",
                            "message": "Failed to run pose estimation",
                        }
                    }
                }
            },
        },
        503: {
            "model": ErrorResponse,
            "description": "サービス利用不可 (ストレージエラーなど)",
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "code": "STORAGE_SERVICE_UNAVAILABLE",
                            "message": "Failed to upload processed video",
                        }
                    }
                }
            },
        },
    },
)
def process_video(
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

    Note:
        FastAPI (Starlette) の仕様により、CPU バウンドな処理や同期 I/O を含むため
        `async def` ではなく `def` で定義し、スレッドプールで実行させています。

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
        # UploadFile.size は SpooledTemporaryFile の実装依存で正確でない場合があるが、
        # Content-Length ヘッダー等から取れる場合もある。
        # ここでは簡易チェックとする。厳密にはストリーム読み込み時にカウントすべき。
        if file.size and file.size > max_size:
            size_mb = file.size / (1024 * 1024)
            max_mb = max_size / (1024 * 1024)
            raise FileTooLargeError(size_mb, max_mb)

        # 2. 一時ファイルに保存 (ストリーム処理)
        filename = file.filename or "video.mp4"
        suffix = Path(filename).suffix or ".mp4"
        input_temp_path = temp_manager.create_temp_path(suffix=suffix)

        with Path(input_temp_path).open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        logger.info("Saved uploaded file to %s", input_temp_path)

        # 3. ユースケース実行 (バリデーション含む)
        output_key = _generate_output_key(filename)
        input_dto = ProcessVideoInput(
            input_path=input_temp_path,
            output_key=output_key,
            score_threshold=score_threshold,
        )

        result = use_case.execute(input_dto)

        # 4. レスポンス変換
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

    except Exception as e:
        # ドメイン例外を API 例外に変換
        raise _convert_to_api_error(e) from e

    finally:
        # 入力一時ファイルのクリーンアップ
        if input_temp_path:
            temp_manager.cleanup(input_temp_path)
        # UploadFile のクローズ
        try:
            file.file.close()
        except Exception:
            logger.warning("Failed to close upload file", exc_info=True)


def _generate_output_key(original_filename: str) -> str:
    """出力ファイルのキーを生成します。"""
    path = Path(original_filename)
    base_name = path.stem
    unique_id = uuid.uuid4().hex[:8]
    return f"processed/{base_name}_{unique_id}.mp4"


def _convert_to_api_error(e: Exception) -> Exception:
    """ドメイン例外を API 例外に変換します。"""
    if isinstance(e, VideoDurationError):
        logger.warning("Video duration error: %s", e)
        if e.duration_sec < MIN_VIDEO_DURATION_SEC:
            return VideoTooShortError(e.duration_sec)
        return VideoTooLongError(e.duration_sec)

    if isinstance(e, VideoProcessingError):
        logger.warning("Video processing error: %s", e)
        return InvalidVideoFormatError(str(e))

    if isinstance(e, PoseEstimationError):
        logger.exception("Pose estimation error")
        return ModelInferenceError(str(e))

    if isinstance(e, StorageError):
        logger.exception("Storage error")
        return StorageServiceUnavailableError(str(e))

    logger.exception("Unexpected error during video processing")
    return ModelInferenceError(f"Unexpected error: {e}")
