# Pose Estimation Backend

AI による姿勢推定アプリケーションのバックエンド API です。ユーザーがアップロードした動画を解析し、骨格検知結果を描画して返します。

## 機能

- **動画アップロード**: `.mp4`, `.mov`, `.avi` 形式に対応
- **姿勢推定**: TensorFlow Hub の MoveNet (Lightning) モデルを使用
- **動画生成**: 推定された骨格を動画にオーバーレイ描画
- **クラウドストレージ**: 処理結果を Cloudflare R2 に保存し、署名付き URL を発行

## 技術スタック

| カテゴリ         | 技術                     | 解説・選定理由                                              |
| :--------------- | :----------------------- | :---------------------------------------------------------- |
| **Language**     | **Python 3.11**          | 型ヒント機能をフル活用し、堅牢なコードベースを構築          |
| **Framework**    | **FastAPI**              | 非同期処理に強く、型安全なモダン Web フレームワーク         |
| **ML Core**      | **TensorFlow / MoveNet** | 軽量かつ高精度な Lightning モデルを採用 (Multi-person 対応) |
| **Image Proc**   | **OpenCV / FFmpeg**      | 効率的なフレーム処理と音声結合                              |
| **Architecture** | **Clean Architecture**   | 依存性の方向を一方向に保ち、テスト容易性を担保              |
| **Quality**      | **Ruff / Mypy / Pytest** | 厳格な静的解析と高いテストカバレッジ基準                    |

## アーキテクチャ設計

本プロジェクトは **Clean Architecture** (Layered Architecture) を採用し、技術的詳細（フレームワークや DB）からビジネスロジックを分離しています。

<details>
<summary><strong>レイヤードアーキテクチャとディレクトリ構造</strong></summary>

### 4層構造

1.  **Domain Layer (`src/posture_estimation/domain`)**
    - ビジネスロジックの中核。外部ライブラリ（TensorFlow, FastAPI 等）に依存しない純粋な Python クラスとインターフェースのみで構成。
2.  **Application Layer (`src/posture_estimation/application`)**
    - ユースケースの実装。ドメインオブジェクトを操作し、具体的な業務フローを実現します。
3.  **Interface Layer (`src/posture_estimation/api`)**
    - REST API コントローラー。HTTP リクエストをユースケースへの入力に変換します。
4.  **Infrastructure Layer (`src/posture_estimation/infrastructure`)**
    - 詳細実装（TensorFlow, OpenCV, Cloudflare R2）。ドメイン層で定義されたインターフェースを実装します。

### ディレクトリ構造

```text
src/
├── posture_estimation/
│   ├── domain/           # 1. Domain (Entities, Value Objects, Interfaces)
│   ├── application/      # 2. Application (Use Cases, Services)
│   ├── api/              # 3. Interface (Routes, Dependencies, Schema)
│   ├── infrastructure/   # 4. Infrastructure (Repositories, ML Impl, Storage)
│   ├── core/             # Shared Kernel (Config, Logging, Exceptions)
│   └── main.py           # Entry Point
```

</details>

<details>
<summary><strong>技術的こだわりと最適化 (ML & Performance)</strong></summary>

### ML 推論最適化

MoveNet の推論速度と精度を最大化するために、以下の最適化を行っています。

| 最適化項目       | 実装詳細                                        | 効果                                             |
| :--------------- | :---------------------------------------------- | :----------------------------------------------- |
| **Graph Mode**   | `@tf.function(reduce_retracing=True)`           | 推論オーバーヘッドを削減し、速度を 2-10倍 向上   |
| **Warm-up**      | 起動時にダミーデータで推論を実行                | 初回リクエスト時のモデルロード遅延（数秒）を解消 |
| **Letterboxing** | アスペクト比を維持したままリサイズ + パディング | 画像の歪みを防ぎ、推論精度を向上                 |

### インフラ層設計パターン

| パターン            | 実装例                     | 利点                                                                    |
| :------------------ | :------------------------- | :---------------------------------------------------------------------- |
| **Stdin Pipe**      | `FFmpegVideoSink`          | 中間ファイルを生成せずパイプ渡しを行うことでディスク I/O を削減         |
| **Factory Pattern** | `IVideoSourceFactory`      | 動画ソースの生成ロジックを抽象化し、DI (依存性注入) を容易に            |
| **Context Manager** | `with VideoProcessor(...)` | Python の `with` 構文でリソース（メモリ、ファイルハンドル）を確実に解放 |

</details>

## セットアップ

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

## API ドキュメント

API の詳細な仕様は以下で確認できます。

- **静的 HTML**: [docs/index.html](docs/index.html)
- **OpenAPI 定義**: [docs/openapi.yaml](docs/openapi.yaml)
- **開発時 (Swagger UI)**: サーバー起動中に `http://localhost:8080/docs` へアクセス

## 環境変数

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

## テスト

```bash
# 全テスト実行
poetry run pytest

# カバレッジレポート
poetry run pytest --cov=posture_estimation
```
