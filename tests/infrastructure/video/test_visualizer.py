"""OpenCVPoseVisualizer のテスト。"""

import numpy as np
import pytest
from numpy.typing import NDArray

from posture_estimation.domain.entities import Pose
from posture_estimation.domain.values import Keypoint, KeypointName, Point2D
from posture_estimation.infrastructure.video.visualizer import OpenCVPoseVisualizer


@pytest.fixture
def blank_image() -> NDArray[np.uint8]:
    """100x100 の黒塗り画像。"""
    return np.zeros((100, 100, 3), dtype=np.uint8)


@pytest.fixture
def sample_pose() -> Pose:
    """描画用のサンプル姿勢データ。"""
    return Pose(
        frame_index=0,
        overall_score=0.9,
        keypoints=[
            # Nose (center)
            Keypoint(
                name=KeypointName.NOSE,
                point=Point2D(x=0.5, y=0.5),
                score=0.9,
            ),
            # Left Eye (slightly left)
            Keypoint(
                name=KeypointName.LEFT_EYE,
                point=Point2D(x=0.4, y=0.4),
                score=0.8,
            ),
            # Low score point (should not be drawn)
            Keypoint(
                name=KeypointName.RIGHT_EYE,
                point=Point2D(x=0.6, y=0.4),
                score=0.1,
            ),
        ],
    )


def test_draw_points(blank_image: NDArray[np.uint8], sample_pose: Pose) -> None:
    """キーポイントが正しく描画されることを確認する。"""
    visualizer = OpenCVPoseVisualizer()
    visualizer.draw(blank_image, [sample_pose])

    # Nose (50, 50) - 緑色 (0, 255, 0)
    # circle radius=4 なので、中心付近は塗られているはず
    assert np.array_equal(blank_image[50, 50], [0, 255, 0])

    # Left Eye (40, 40)
    assert np.array_equal(blank_image[40, 40], [0, 255, 0])

    # Right Eye (60, 40) - Low score なので描画されない (黒のまま)
    assert np.array_equal(blank_image[40, 60], [0, 0, 0])


def test_draw_edges(blank_image: NDArray[np.uint8]) -> None:
    """エッジ (接続線) が描画されることを確認する。"""
    # 0(Nose) と 1(Left Eye) は接続されているはず (Edge定義による)
    pose = Pose(
        frame_index=0,
        overall_score=1.0,
        keypoints=[
            # 0: Nose
            Keypoint(KeypointName.NOSE, Point2D(0.5, 0.5), 0.9),
            # 1: Left Eye
            Keypoint(KeypointName.LEFT_EYE, Point2D(0.5, 0.6), 0.9),
            # Dummy filler for indices 2-16 to avoid index error if visualizer iterates all
            # (Visualizer loop is based on existing keypoints or indices?)
            # Implementation iterates enumerate(pose.keypoints), so we need indices to match
            # Visualizer relies on index in list. So we need at least up to index 1.
        ],
    )
    # Note: Visualizer uses 'enumerate', so list indices matter.
    # To test edge (0, 1), we need keypoints at index 0 and 1.

    visualizer = OpenCVPoseVisualizer()
    visualizer.draw(blank_image, [pose])

    # 線分の中点 (50, 55) が塗られているか確認
    # (50, 50) to (50, 60)
    assert np.array_equal(blank_image[55, 50], [0, 255, 0])


def test_draw_boundary_clipping(blank_image: NDArray[np.uint8]) -> None:
    """画像境界上の座標 (1.0) が正しくクリップされ、エラーにならないことを確認する。"""
    pose = Pose(
        frame_index=0,
        overall_score=1.0,
        keypoints=[
            # x=1.0, y=1.0 -> 100x100 画像では (100, 100) になるが、index は 99 まで。
            # min(width-1, px) により (99, 99) になるはず。
            Keypoint(KeypointName.NOSE, Point2D(1.0, 1.0), 0.9),
        ],
    )

    visualizer = OpenCVPoseVisualizer()
    visualizer.draw(blank_image, [pose])

    # 右下 (99, 99) に描画されているはず
    assert np.array_equal(blank_image[99, 99], [0, 255, 0])
