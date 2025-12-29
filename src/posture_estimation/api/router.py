"""API ルーター定義。"""

from typing import Annotated

from fastapi import APIRouter, File, Form, UploadFile

from posture_estimation.api.schemas import (
    ErrorResponse,
    HealthResponse,
    ProcessVideoResponse,
)

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
    score_threshold: Annotated[
        float,
        Form(
            description="姿勢検出の閾値 (0.0-1.0)",
            ge=0.0,
            le=1.0,
        )
    ] = 0.2,
) -> ProcessVideoResponse:
    """動画処理エンドポイント。

    Args:
        file: アップロードされた動画ファイル
        score_threshold: 姿勢検出の閾値

    Returns:
        処理結果 (署名付き URL, メタデータ, 統計情報)

    Raises:
        InvalidVideoFormatError: 動画フォーマットが無効な場合
        VideoTooShortError: 動画が短すぎる場合
        VideoTooLongError: 動画が長すぎる場合
        FileTooLargeError: ファイルサイズ超過の場合
        InvalidParameterError: パラメータが不正な場合
        ModelInferenceError: 推論エラーの場合
        StorageServiceUnavailableError: ストレージエラーの場合
    """
    # Task 5-2 で実装
    raise NotImplementedError("Implementation in Task 5-2")
