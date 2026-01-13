import pytest
from fastapi.testclient import TestClient

from posture_estimation.main import app


@pytest.fixture
def client() -> TestClient:
    """TestClient のフィクスチャ。

    Returns:
        TestClient: FastAPI アプリケーションのテストクライアント
    """
    return TestClient(app)
