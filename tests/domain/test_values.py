from posture_estimation.domain.values import Keypoint, KeypointName, Point2D, VideoMeta


def test_videometa_initialization() -> None:
    """VideoMeta の初期化と属性を確認する。"""
    meta = VideoMeta(
        width=1920,
        height=1080,
        fps=30.0,
        total_frames=300,
        duration_sec=10.0,
        has_audio=True,
    )

    assert meta.width == 1920
    assert meta.height == 1080
    assert meta.fps == 30.0
    assert meta.total_frames == 300
    assert meta.duration_sec == 10.0
    assert meta.has_audio is True


def test_keypoint_initialization() -> None:
    """Keypoint の初期化と属性を確認する。"""
    point = Point2D(x=0.5, y=0.5)
    kp = Keypoint(name=KeypointName.NOSE, point=point, score=0.95)

    assert kp.name == KeypointName.NOSE
    assert kp.point.x == 0.5
    assert kp.point.y == 0.5
    assert kp.score == 0.95
