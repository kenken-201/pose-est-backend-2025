# Pose Estimation Backend

AI による姿勢推定アプリケーションのバックエンド API です。ユーザーがアップロードした動画を解析し、骨格検知結果を描画して返します。

## 🚀 機能

- **動画アップロード**: `.mp4`, `.mov`, `.avi` 形式に対応
- **姿勢推定**: TensorFlow Hub の MoveNet (Lightning) モデルを使用
- **動画生成**: 推定された骨格を動画にオーバーレイ描画
- **クラウドストレージ**: 処理結果を Cloudflare R2 に保存し、署名付き URL を発行

## 🛠 技術スタック

- **言語**: Python 3.11
- **フレームワーク**: FastAPI
- **ML ライブラリ**: TensorFlow, TensorFlow Hub
- **画像処理**: OpenCV, ffmpeg-python
- **インフラ**: Cloud Run (予定), Cloudflare R2
- **開発ツール**: Poetry, Docker, Ruff, Mypy, Pytest

## 📦 セットアップ

### 必要要件

- Docker & Docker Compose (または Colima)
- Python 3.11+ (ローカル開発時)
- Poetry

### Docker での実行 (推奨)

```bash
# 環境変数の設定 (例をコピー)
cp .env.example .env
# 必要に応じて .env を編集してください

# 起動
docker-compose up --build
```

API は `http://localhost:8080` で利用可能です。

- ヘルスチェック: `http://localhost:8080/api/v1/health`
- API ドキュメント: `http://localhost:8080/docs`

### ローカル開発環境のセットアップ

```bash
# 依存関係のインストール
poetry install

# 開発サーバー起動
poetry run uvicorn posture_estimation.main:app --reload
```

## � API ドキュメント

API の詳細な仕様は以下で確認できます。

- **静的 HTML**: [docs/index.html](docs/index.html) (ブラウザで直接開けます)
- **OpenAPI 定義**: [docs/openapi.yaml](docs/openapi.yaml)
- **開発時 (Swagger UI)**: サーバー起動中に `http://localhost:8080/docs` へアクセス

## �🔑 環境変数

| 変数名               | 説明                   | デフォルト値       |
| -------------------- | ---------------------- | ------------------ |
| `ML_MODEL_URL`       | MoveNet モデル URL     | (Lightning モデル) |
| `ML_SCORE_THRESHOLD` | 検出信頼度の閾値       | 0.3                |
| `R2_ENDPOINT_URL`    | R2 エンドポイント URL  | 必須               |
| `R2_ACCESS_KEY`      | R2 アクセスキー        | 必須               |
| `R2_SECRET_KEY`      | R2 シークレット        | 必須               |
| `R2_BUCKET_NAME`     | 保存先バケット名       | 必須               |
| `CORS_ORIGINS`       | CORS 許可オリジン      | \*                 |
| `MAX_UPLOAD_SIZE_MB` | アップロード最大サイズ | 100                |

## 🧪 テスト

```bash
# 全テスト実行
poetry run pytest

# カバレッジレポート
poetry run pytest --cov=posture_estimation
```

## 📁 ディレクトリ構造

```
src/posture_estimation/
├── api/            # Web API (Router, Schema, Dependencies)
├── application/    # アプリケーション層 (Use Cases, DTOs)
├── domain/         # ドメイン層 (Entities, Interfaces)
├── infrastructure/ # インフラ層 (ML, Storage, Video)
├── core/           # 共通設定 (DI Container)
└── main.py         # エントリーポイント
```
