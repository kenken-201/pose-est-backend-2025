from fastapi import FastAPI
from fastapi.testclient import TestClient

from posture_estimation.api.middleware import CloudflareAuthMiddleware


def test_auth_success(monkeypatch):
    """正しいトークンでアクセスできること。"""
    monkeypatch.setenv("CLOUDFLARE_ACCESS_TOKEN", "valid-token")

    app = FastAPI()
    app.add_middleware(CloudflareAuthMiddleware)

    @app.get("/")
    def read_root():
        return {"msg": "ok"}

    client = TestClient(app)
    headers = {"X-CF-Access-Token": "valid-token"}
    response = client.get("/", headers=headers)
    assert response.status_code == 200
    assert response.json() == {"msg": "ok"}


def test_auth_failure(monkeypatch):
    """不正なトークンでアクセス拒否されること。"""
    monkeypatch.setenv("CLOUDFLARE_ACCESS_TOKEN", "valid-token")

    app = FastAPI()
    app.add_middleware(CloudflareAuthMiddleware)

    @app.get("/")
    def read_root():
        return {"msg": "ok"}

    client = TestClient(app)
    headers = {"X-CF-Access-Token": "invalid-token"}
    response = client.get("/", headers=headers)
    assert response.status_code == 403
    assert "Forbidden" in response.text


def test_auth_missing_header_failure(monkeypatch):
    """トークンヘッダーがない場合も拒否されること。"""
    monkeypatch.setenv("CLOUDFLARE_ACCESS_TOKEN", "valid-token")

    app = FastAPI()
    app.add_middleware(CloudflareAuthMiddleware)

    @app.get("/")
    def read_root():
        return {"msg": "ok"}

    client = TestClient(app)
    response = client.get("/")  # ヘッダーなし
    assert response.status_code == 403


def test_auth_disabled_when_env_not_set(monkeypatch):
    """環境変数が設定されていない場合、認証がスキップされること。"""
    monkeypatch.delenv("CLOUDFLARE_ACCESS_TOKEN", raising=False)

    app = FastAPI()
    app.add_middleware(CloudflareAuthMiddleware)

    @app.get("/")
    def read_root():
        return {"msg": "ok"}

    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200


def test_health_endpoint_bypass(monkeypatch):
    """ヘルスチェックは認証なしでアクセスできること。"""
    monkeypatch.setenv("CLOUDFLARE_ACCESS_TOKEN", "valid-token")

    app = FastAPI()
    app.add_middleware(CloudflareAuthMiddleware)

    @app.get("/api/v1/health")  # 実際のパスに合わせて検証 (/health で終わるパス)
    def health():
        return {"status": "ok"}

    client = TestClient(app)
    response = client.get("/api/v1/health")
    assert response.status_code == 200


def test_options_bypass(monkeypatch):
    """OPTIONS メソッドは認証なしでアクセスできること。"""
    monkeypatch.setenv("CLOUDFLARE_ACCESS_TOKEN", "valid-token")

    app = FastAPI()
    app.add_middleware(CloudflareAuthMiddleware)

    @app.get("/")
    def read_root():
        pass

    @app.options("/")
    def options_root():
        return {}

    client = TestClient(app)
    response = client.options("/")
    assert response.status_code == 200
