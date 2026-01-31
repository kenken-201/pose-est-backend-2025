# Builder Stage
FROM python:3.11-slim as builder

WORKDIR /app

# uv のインストール
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# 設定ファイルのコピー
COPY pyproject.toml uv.lock ./

# 依存関係を requirements.txt にエクスポート
RUN uv export --frozen --no-emit-workspace --output-file requirements.txt

# Runtime Stage
FROM python:3.11-slim as runtime

WORKDIR /app

# 環境変数の設定
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src \
    # CPU 環境向けの TensorFlow 最適化
    TF_CPP_MIN_LOG_LEVEL=2 \
    CUDA_VISIBLE_DEVICES=-1

# システム依存パッケージのインストール
# libgl1: 削除済み (opencv-python-headless では不要)
# libglib2.0-0: opencv-python-headless に必要
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    curl \
    ffmpeg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Python 依存パッケージのインストール (Builder からコピー)
# BuildKit キャッシュマウントで再ビルドを高速化しつつ、--no-cache-dir でイメージサイズを抑制
COPY --from=builder /app/requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -r requirements.txt

# ソースコードのコピー
COPY src ./src

# 非 root ユーザーの作成
RUN addgroup --system appgroup && adduser --system --group appuser
USER appuser

# ポート開放
EXPOSE 8080

# ヘルスチェック (任意だが推奨)
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD ["curl", "-f", "http://localhost:8080/api/v1/health"]

# アプリケーションの実行
CMD ["uvicorn", "posture_estimation.main:app", "--host", "0.0.0.0", "--port", "8080"]
