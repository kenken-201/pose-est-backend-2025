from dataclasses import dataclass

from posture_estimation.domain.values import VideoMeta


@dataclass(frozen=True)
class ProcessVideoInput:
    """動画処理ユースケースの入力パラメータ。"""

    input_path: str
    """入力動画のパス (ローカルファイルまたは一時ファイル)。"""
    
    output_key: str
    """保存先（R2）のキー。"""
    
    score_threshold: float = 0.2
    """姿勢検出の閾値。"""


@dataclass(frozen=True)
class ProcessVideoResult:
    """動画処理ユースケースの出力結果。"""

    signed_url: str
    """処理済み動画の署名付き URL。"""
    
    video_meta: VideoMeta
    """動画のメタデータ。"""
    
    total_poses: int
    """検出された延べ姿勢数。"""
    
    processing_time_sec: float
    """処理にかかった時間 (秒)。"""
