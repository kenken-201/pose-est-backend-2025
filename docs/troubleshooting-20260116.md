# トラブルシューティングレポート (2026-01-16)

## 概要

動画アップロード機能の開発環境 (`dev.kenken-pose-est.online` / `api-dev.kenken-pose-est.online`) へのデプロイ検証時に発生したエラーとその調査結果をまとめます。

## 発生した事象

### 1. HTTP 422 Unprocessable Entity

- **現象**: フロントエンドからアップロードリクエスト送信後に発生。
- **原因**: リクエストパラメータの不一致。
  - フロントエンド送信: `multipart/form-data` のフィールド名 `video`
  - バックエンド期待値 (`openapi.yaml`): フィールド名 `file`
- **対応**: フロントエンド側でフィールド名を `file` に修正し解決済み。

### 2. HTTP 500 Internal Server Error (R2 Unauthorized)

- **現象**: ファイルアップロード自体は成功するが、その後の姿勢推定処理開始時（またはファイル保存時）に発生。
- **エラーログ**:
  ```
  S3UploadFailedError: Failed to upload .../xxx.mp4 to pose-est-videos-prod/processed/xxx.mp4:
  An error occurred (Unauthorized) when calling the PutObject operation: Unauthorized
  ```
- **調査結果**:
  - Cloud Run 上のバックエンドアプリケーションから Cloudflare R2 バケット (`pose-est-videos-prod`) への書き込み権限がない、または認証に失敗している。
  - 開発環境 (`api-dev`) が **本番用バケット (`pose-est-videos-prod`)** に書き込もうとしている点も要確認（環境変数の設定ミス、あるいは意図的な構成か）。

## 推奨される対応アクション

1. **Cloud Run 環境変数の確認**: `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY` が正しく設定されているか。
2. **R2 API トークンの権限確認**: トークンに `PutObject` (書き込み) 権限が付与されているか。
3. **接続先バケットの確認**: 開発環境が 本番バケット `pose-est-videos-prod` を使用するのが正しい構成か再考する（通常は `pose-est-videos-dev` 等を使用すべき）。
