import pytest

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


def test_point2d_validation_invalid_x() -> None:
    """Point2D の x 座標が範囲外の場合に ValueError を発生させる。"""
    with pytest.raises(ValueError, match=r"x must be between 0.0 and 1.0"):
        Point2D(x=1.5, y=0.5)


def test_point2d_validation_invalid_y() -> None:
    """Point2D の y 座標が範囲外の場合に ValueError を発生させる。"""
    with pytest.raises(ValueError, match=r"y must be between 0.0 and 1.0"):
        Point2D(x=0.5, y=-0.1)


def test_keypoint_validation_invalid_score() -> None:
    """Keypoint の score が範囲外の場合に ValueError を発生させる。"""
    point = Point2D(x=0.5, y=0.5)
    with pytest.raises(ValueError, match=r"score must be between 0.0 and 1.0"):
        Keypoint(name=KeypointName.NOSE, point=point, score=1.5)


def test_point2d_boundary_values() -> None:
    """Point2D の境界値 (0.0, 1.0) が正常に受け入れられることを確認する。"""
    p_min = Point2D(x=0.0, y=0.0)
    p_max = Point2D(x=1.0, y=1.0)
    assert p_min.x == 0.0
    assert p_max.y == 1.0
