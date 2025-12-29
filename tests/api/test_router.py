"""API ルーターの E2E テスト。"""

import io
from collections.abc import Generator
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from posture_estimation.api.dependencies import (
    get_process_video_use_case,
    get_temp_manager,
)
from posture_estimation.application.dtos import ProcessVideoResult
from posture_estimation.domain.exceptions import VideoDurationError
from posture_estimation.domain.values import VideoMeta
from posture_estimation.main import app


@pytest.fixture
def mock_use_case() -> MagicMock:
    """ProcessVideoUseCase のモック。"""
    mock = MagicMock()
    mock.execute.return_value = ProcessVideoResult(
        signed_url="https://example.com/signed-url",
        video_meta=VideoMeta(
            width=1920,
            height=1080,
            fps=30.0,
            total_frames=150,
            duration_sec=5.0,
            has_audio=True,
        ),
        total_poses=100,
        processing_time_sec=2.5,
    )
    return mock


@pytest.fixture
def mock_temp_manager() -> MagicMock:
    """TempFileManager のモック。"""
    mock = MagicMock()
    mock.create_temp_path.return_value = "/tmp/test_video.mp4"  # noqa: S108
    mock.cleanup.return_value = True
    return mock


@pytest.fixture
def test_client(
    mock_use_case: MagicMock,
    mock_temp_manager: MagicMock,
) -> Generator[TestClient, None, None]:
    """テストクライアント (依存関係をオーバーライド)。"""
    app.dependency_overrides[get_process_video_use_case] = lambda: mock_use_case
    app.dependency_overrides[get_temp_manager] = lambda: mock_temp_manager

    yield TestClient(app)

    app.dependency_overrides.clear()


def test_health_check(test_client: TestClient) -> None:
    """ヘルスチェックエンドポイントが正常に動作することを確認する。"""
    response = test_client.get("/api/v1/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_process_video_success(
    test_client: TestClient,
    mock_use_case: MagicMock,
    mock_temp_manager: MagicMock,
) -> None:
    """正常系: 動画処理が成功することを確認する。"""
    # ダミー動画データ
    video_content = b"dummy video content"
    files = {"file": ("test.mp4", io.BytesIO(video_content), "video/mp4")}
    data = {"score_threshold": "0.3"}

    response = test_client.post("/api/v1/process", files=files, data=data)

    assert response.status_code == 200
    result = response.json()
    assert result["signed_url"] == "https://example.com/signed-url"
    assert result["video_meta"]["width"] == 1920
    assert result["total_poses"] == 100

    # UseCase が呼ばれたことを確認
    mock_use_case.execute.assert_called_once()

    # クリーンアップが呼ばれたことを確認
    mock_temp_manager.cleanup.assert_called()


def test_process_video_invalid_threshold(test_client: TestClient) -> None:
    """異常系: score_threshold が範囲外の場合にエラーを返すことを確認する。"""
    video_content = b"dummy video content"
    files = {"file": ("test.mp4", io.BytesIO(video_content), "video/mp4")}
    data = {"score_threshold": "1.5"}  # 範囲外

    response = test_client.post("/api/v1/process", files=files, data=data)

    assert response.status_code == 422  # Validation error


def test_process_video_too_short(
    test_client: TestClient,
    mock_use_case: MagicMock,
) -> None:
    """異常系: 動画が短すぎる場合 (VideoDurationError) にエラーを返すことを確認する。"""
    # UseCase が VideoDurationError を投げるように設定
    mock_use_case.execute.side_effect = VideoDurationError("Video too short", 0.5)

    video_content = b"dummy video content"
    files = {"file": ("test.mp4", io.BytesIO(video_content), "video/mp4")}

    response = test_client.post("/api/v1/process", files=files)

    # 400 Bad Request に変換されているはず
    assert response.status_code == 400
    error = response.json()["error"]
    assert "Video too short" in error["message"]


def test_process_video_too_long(
    test_client: TestClient,
    mock_use_case: MagicMock,
) -> None:
    """異常系: 動画が長すぎる場合 (VideoDurationError) にエラーを返すことを確認する。"""
    # UseCase が VideoDurationError を投げるように設定
    mock_use_case.execute.side_effect = VideoDurationError("Video too long", 1000.0)

    video_content = b"dummy video content"
    files = {"file": ("test.mp4", io.BytesIO(video_content), "video/mp4")}

    response = test_client.post("/api/v1/process", files=files)

    assert response.status_code == 400
    error = response.json()["error"]
    assert "Video too long" in error["message"]
