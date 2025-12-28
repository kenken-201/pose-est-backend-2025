from dataclasses import dataclass, field

from posture_estimation.domain.values import Keypoint, VideoMeta


@dataclass
class Pose:
    """1フレーム内で検出された単一の姿勢を表すエンティティ。

    Attributes:
        frame_index (int): フレーム番号 (0始まり)
        keypoints (list[Keypoint]): 検出されたキーポイントのリスト
    """

    frame_index: int
    keypoints: list[Keypoint]


@dataclass
class AnalyzedVideo:
    """姿勢推定による動画の解析結果全体を表す集約ルート (Aggregate Root)。

    Attributes:
        video_path (str): 解析対象の動画ファイルパス (識別子として機能)
        meta (VideoMeta): 動画のメタデータ
        poses (list[Pose]): 各フレームの解析結果リスト
    """

    video_path: str
    meta: VideoMeta
    poses: list[Pose] = field(default_factory=list)

    def add_pose(self, pose: Pose) -> None:
        """解析された姿勢を結果に追加します。

        Args:
            pose (Pose): 追加する姿勢データ
        """
        self.poses.append(pose)
