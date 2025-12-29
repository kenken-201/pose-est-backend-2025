from dataclasses import dataclass, field

from posture_estimation.domain.values import Keypoint, VideoMeta


@dataclass
class Pose:
    """1フレーム内で検出された単一の姿勢を表すエンティティ。

    Attributes:
        frame_index (int): フレーム番号 (0始まり)
        keypoints (list[Keypoint]): 検出されたキーポイントのリスト
        overall_score (float): 姿勢全体の信頼度スコア (0.0-1.0)
    """

    frame_index: int
    keypoints: list[Keypoint]
    overall_score: float = 0.0


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

    def get_poses_for_frame(self, frame_index: int) -> list[Pose]:
        """指定されたフレーム番号の姿勢リストを取得します。

        Args:
            frame_index (int): フレーム番号

        Returns:
            list[Pose]: 該当フレームで検出された姿勢のリスト
        """
        return [p for p in self.poses if p.frame_index == frame_index]
