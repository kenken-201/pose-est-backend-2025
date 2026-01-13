# デプロイメントガイド

このドキュメントでは、アプリケーションのコンテナ化と実行方法について説明します。

## 前提条件

- **Colima** (macOS): Docker ランタイムとして使用します。
- **Docker CLI**: コマンドラインツールが必要です。
- **Docker Compose**: コンテナオーケストレーションに使用します。

### セットアップ (macOS)

`colima` と `docker` CLI が必要です。以下のコマンドでインストールできます。

```bash
brew install colima docker docker-compose
```

Colima の起動:

```bash
# x86_64 エミュレーションが必要な場合 (TensorFlow 等)
colima start --arch x86_64 --memory 4

# または標準起動
colima start --cpu 4 --memory 8
```

## ローカルでの実行

`docker-compose` を使用してアプリケーションを起動します。

```bash
# ビルドと起動
colima start
docker-compose up --build

# バックグラウンド実行
docker-compose up -d
```

API は `http://localhost:8080` で利用可能です。

- ヘルスチェック: `http://localhost:8080/api/v1/health`
- API ドキュメント: `http://localhost:8080/docs`

## 環境変数

`.env` ファイルを作成するか、`docker-compose.yml` の環境変数を設定してください。

- `ML_MODEL_URL`: TensorFlow Hub モデル URL
- `R2_ENDPOINT_URL`: Cloudflare R2 エンドポイント
- `R2_ACCESS_KEY`: R2 アクセスキー
- `R2_SECRET_KEY`: R2 シークレットキー
- `R2_BUCKET_NAME`: R2 バケット名
