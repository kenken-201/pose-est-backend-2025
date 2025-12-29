from posture_estimation.domain.entities import AnalyzedVideo, Pose
from posture_estimation.domain.values import (
    Keypoint,
    KeypointName,
    Point2D,
    VideoMeta,
)


def test_analyzed_video_add_pose() -> None:
    """AnalyzedVideo に Pose を追加できるか確認する。"""
    meta = VideoMeta(
        width=1280,
        height=720,
        fps=30.0,
        total_frames=100,
        duration_sec=3.33,
        has_audio=False,
    )
    video = AnalyzedVideo(video_path="test.mp4", meta=meta)

    pose1 = Pose(frame_index=0, keypoints=[], overall_score=0.9)
    video.add_pose(pose1)

    assert len(video.poses) == 1
    assert video.poses[0] == pose1


def test_get_poses_for_frame() -> None:
    """get_poses_for_frame が正しくフィルタリングするか確認する。"""
    meta = VideoMeta(
        width=1280,
        height=720,
        fps=30.0,
        total_frames=100,
        duration_sec=3.33,
    )
    video = AnalyzedVideo(video_path="test.mp4", meta=meta)

    # フレーム0に2つのPose (複数人)
    kp = Keypoint(
        name=KeypointName.NOSE, point=Point2D(0.5, 0.5), score=0.9
    )  # Dummy KP
    pose_frame0_1 = Pose(
        frame_index=0, keypoints=[kp], overall_score=0.9
    )
    pose_frame0_2 = Pose(
        frame_index=0, keypoints=[kp], overall_score=0.8
    )
    # フレーム1に1つのPose
    pose_frame1_1 = Pose(
        frame_index=1, keypoints=[kp], overall_score=0.95
    )

    video.add_pose(pose_frame0_1)
    video.add_pose(pose_frame0_2)
    video.add_pose(pose_frame1_1)

    # フレーム0のPoseを取得
    poses_frame0 = video.get_poses_for_frame(0)
    assert len(poses_frame0) == 2
    assert pose_frame0_1 in poses_frame0
    assert pose_frame0_2 in poses_frame0

    # フレーム1のPoseを取得
    poses_frame1 = video.get_poses_for_frame(1)
    assert len(poses_frame1) == 1
    assert poses_frame1[0] == pose_frame1_1

    # 存在しないフレーム
    assert len(video.get_poses_for_frame(99)) == 0


def test_pose_validation_invalid_frame_index() -> None:
    """Pose の frame_index が負の場合に ValueError を発生させる。"""
    import pytest

    with pytest.raises(ValueError, match=r"frame_index must be >= 0"):
        Pose(frame_index=-1, keypoints=[], overall_score=0.5)


def test_pose_validation_invalid_overall_score() -> None:
    """Pose の overall_score が範囲外の場合に ValueError を発生させる。"""
    import pytest

    with pytest.raises(ValueError, match=r"overall_score must be between 0.0 and 1.0"):
        Pose(frame_index=0, keypoints=[], overall_score=1.5)
