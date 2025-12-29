from dataclasses import dataclass
from enum import Enum


class KeypointName(str, Enum):
    """MoveNet が検出する 17 種類のキーポイント名。"""

    NOSE = "nose"
    LEFT_EYE = "left_eye"
    RIGHT_EYE = "right_eye"
    LEFT_EAR = "left_ear"
    RIGHT_EAR = "right_ear"
    LEFT_SHOULDER = "left_shoulder"
    RIGHT_SHOULDER = "right_shoulder"
    LEFT_ELBOW = "left_elbow"
    RIGHT_ELBOW = "right_elbow"
    LEFT_WRIST = "left_wrist"
    RIGHT_WRIST = "right_wrist"
    LEFT_HIP = "left_hip"
    RIGHT_HIP = "right_hip"
    LEFT_KNEE = "left_knee"
    RIGHT_KNEE = "right_knee"
    LEFT_ANKLE = "left_ankle"
    RIGHT_ANKLE = "right_ankle"


@dataclass(frozen=True)
class Point2D:
    """2次元平面上の座標を表す値オブジェクト。

    Attributes:
        x (float): X座標 (正規化された値 0.0-1.0)
        y (float): Y座標 (正規化された値 0.0-1.0)
    """

    x: float
    y: float

    def __post_init__(self) -> None:
        """座標値の範囲をバリデーションします。"""
        if not (0.0 <= self.x <= 1.0):
            msg = f"x must be between 0.0 and 1.0, got {self.x}"
            raise ValueError(msg)
        if not (0.0 <= self.y <= 1.0):
            msg = f"y must be between 0.0 and 1.0, got {self.y}"
            raise ValueError(msg)


@dataclass(frozen=True)
class Keypoint:
    """検出された単一のキーポイントを表す値オブジェクト。

    Attributes:
        name (KeypointName): キーポイントの部位名
        point (Point2D): 座標
        score (float): 検出の信頼度スコア (0.0-1.0)
    """

    name: KeypointName
    point: Point2D
    score: float

    def __post_init__(self) -> None:
        """スコアの範囲をバリデーションします。"""
        if not (0.0 <= self.score <= 1.0):
            msg = f"score must be between 0.0 and 1.0, got {self.score}"
            raise ValueError(msg)


@dataclass(frozen=True)
class VideoMeta:
    """動画ファイルのメタデータを表す値オブジェクト。

    Attributes:
        width (int): 動画の幅 (ピクセル)
        height (int): 動画の高さ (ピクセル)
        fps (float): フレームレート (frames per second)
        total_frames (int): 総フレーム数
        duration_sec (float): 動画の長さ (秒)
        has_audio (bool): 音声トラックが含まれているか
    """

    width: int
    height: int
    fps: float
    total_frames: int
    duration_sec: float
    has_audio: bool = False
