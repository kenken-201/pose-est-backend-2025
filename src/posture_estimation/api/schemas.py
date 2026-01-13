"""API スキーマ定義 (Pydantic)。"""

from pydantic import BaseModel, Field


class VideoMetaResponse(BaseModel):
    """動画メタデータのレスポンススキーマ。"""

    width: int = Field(..., description="動画の幅 (ピクセル)")
    height: int = Field(..., description="動画の高さ (ピクセル)")
    fps: float = Field(..., description="フレームレート")
    duration_sec: float = Field(..., description="動画時間 (秒)")
    has_audio: bool = Field(..., description="音声トラックの有無")


class ProcessVideoResponse(BaseModel):
    """動画処理結果のレスポンススキーマ。"""

    signed_url: str = Field(..., description="処理済み動画の署名付き URL")
    video_meta: VideoMetaResponse = Field(..., description="動画メタデータ")
    total_poses: int = Field(..., description="検出された延べ姿勢数")
    processing_time_sec: float = Field(..., description="処理時間 (秒)")


class HealthResponse(BaseModel):
    """ヘルスチェックのレスポンススキーマ。"""

    status: str = Field(..., description="ステータス (healthy)")
    version: str = Field(..., description="API バージョン")


class ErrorDetail(BaseModel):
    """エラー詳細スキーマ。"""

    code: str = Field(..., description="エラーコード")
    message: str = Field(..., description="エラーメッセージ")


class ErrorResponse(BaseModel):
    """エラーレスポンススキーマ。"""

    error: ErrorDetail = Field(..., description="エラー詳細")
