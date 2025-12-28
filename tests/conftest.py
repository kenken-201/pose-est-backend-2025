import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "../src"))

import pytest
from fastapi.testclient import TestClient
from posture_estimation.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)
