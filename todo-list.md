# 🐍 バックエンド開発進捗 (Navigator-Driver Model)

本プロジェクトは **Navigator（ユーザー）** と **Driver（AI）** の協業モデルで進行します。
各タスクは **「設計・提案」→「承認」→「実装・テスト」→「レビュー」** のサイクルで実行されます。

---

## 📁 フェーズ 1: プロジェクト基盤と品質規格の策定

### ✅ タスク 1-1: 開発環境と品質ツールの設計

- **Goal**: 堅牢な Python 開発環境の定義
- [x] `pyproject.toml` の依存関係定義（FastAPI, TensorFlow, Dev Tools）提案
- [x] 静的解析ツール（Ruff, Mypy）とテストツール（Pytest）の設定方針策定
- [x] **🛑 [Review] 設定ファイルのドラフト承認**

### ✅ タスク 1-2: 基盤実装

- **Goal**: クリーンなプロジェクト初期化
- [x] 設定ファイルの実装 (`pyproject.toml`, `ruff.toml`, `mypy.ini`)
- [x] `commit-msg` フック等のセットアップ（pre-commit）
- [x] Hello World レベルの動作確認（環境健全性チェック）
- [x] **🛑 [Review] 環境構築と初期動作の確認**

---

## 🏗️ フェーズ 2: 抽象・インターフェース設計 (Domain Layer)

### ✅ タスク 2-1: ドメインモデルとインターフェースの設計

- **Goal**: ビジネスロジックの核となる型と契約の定義
- [x] Value Objects 設計 (`Keypoint`, `VideoMeta`)
- [x] Entity/Aggregate 設計 (`Pose`, `AnalyzedVideo`)
- [x] Domain Interfaces 設計 (`IPoseEstimator`, `IVideoSource`)
- [x] **🛑 [Review] ドメイン設計の承認**

### ✅ タスク 2-2: ドメイン層の実装 (TDD)

- **Goal**: 純粋な Python コードによるドメインロジック実装
- [x] Value Objects 拡張
  - [x] `Pose` に全体信頼度スコア (`overall_score`) 追加
  - [x] `VideoMeta` に `has_audio` フラグ追加
- [x] Entities 拡張
  - [x] `AnalyzedVideo` に複数人対応のヘルパーメソッド追加 (例: `get_poses_for_frame`)
- [x] Interfaces 拡張
  - [x] `IStorageService` 追加 (R2 アップロード, 署名 URL 発行)
  - [x] `IVideoSink` 追加 (処理済み動画の書き出し)
- [x] Domain Exceptions 定義
  - [x] `DomainError` 基底クラス
  - [x] `VideoProcessingError`, `StorageError` 等
- [x] 単体テスト
  - [x] `values.py` のテスト (バリデーション)
  - [x] `entities.py` のテスト (ロジック)
- [x] **🛑 [Review] ドメイン実装と型安全性の確認**

---

## 🧠 フェーズ 3: コア機能・インフラ実装 (Infrastructure Layer)

### ✅ タスク 3-1: インフラストラクチャ設計

- **Goal**: 外部システム（ML モデル, OpenCV, Storage）との連携設計
- [x] MoveNet 推定エンジン設計
  - [x] `MoveNetPoseEstimator` クラス設計 (Singleton, Multi-person)
  - [x] スコア閾値フィルタリング戦略
- [x] 動画処理パイプライン設計
  - [x] `OpenCVVideoSource` 設計 (読み込み + メタデータ)
  - [x] `OpenCVVideoSink` 設計 (フレーム書き出し)
  - [x] `FFmpegAudioMerger` 設計 (音声結合)
- [x] ストレージサービス設計
  - [x] `R2StorageService` 設計 (Boto3/S3 互換)
  - [x] `TempFileManager` 設計 (一時ファイル管理)
- [x] **🛑 [Review] インフラ設計の承認**

### ✅ タスク 3-2: ML エンジンと動画処理の実装 (TDD)

- **Goal**: MoveNet と OpenCV/FFmpeg の統合
- [x] `MoveNetPoseEstimator` の実装（複数人対応）とテスト
  - [x] @tf.function によるグラフモード最適化
  - [x] Letterboxing による入力リサイズ（アスペクト比維持）
  - [x] Warm-up による初回推論遅延解消
  - [x] 座標逆変換による元画像座標系への復元
- [x] `VideoProcessor` 実装（音声保持・結合ロジック）
  - [x] Source/Sink 実装 (OpenCV)
  - [x] Audio Merger 実装 (FFmpeg)
  - [x] Context Manager 対応 (`with` 構文)
- [x] `R2StorageService` 実装（アップロード・URL 発行）
  - [x] Adaptive リトライ設定
- [x] `TempFileManager` 実装
  - [x] ロギング追加
  - [x] Context Manager 対応
- [x] **🛑 [Review] 姿勢推定精度と音声保持・R2 保存の確認**

---

## 🔧 フェーズ 4: アプリケーション・統合 (Application Layer)

### ✅ タスク 4-1: ユースケース設計

- **Goal**: アプリケーションの振る舞い（処理フロー）の定義
- [x] `ProcessVideoUseCase` のフロー設計
  - [x] 入出力 DTO 定義 (`ProcessVideoInput`, `ProcessVideoResult`)
  - [x] シーケンス図作成
- [x] エラーハンドリング戦略定義
  - [x] クリーンアップ保証 (try-finally)
  - [x] フレームスキップロジック
- [x] DI（依存性注入）コンテナの構成設計
- [x] **🛑 [Review] ユースケース設計の承認**

### ✅ タスク 4-2: アプリケーションサービス実装 (TDD)

- **Goal**: ユースケース実装とテストによる品質保証
- [x] DTO 定義 (済)
- [x] `ProcessVideoUseCase` 基本実装
  - [x] フレーム処理ループ
  - [x] 姿勢推定 + 描画
  - [x] 一時ファイル管理
- [x] 音声結合統合
- [x] R2 アップロード統合
- [x] エラーハンドリング
- [x] DI コンテナ (`AppContainer`)
- [x] 統合テスト (単体テストでの動作確認完了)
- [x] **🛑 [Review] アプリケーションロジックの確認**

---

## 🔌 フェーズ 5: API インターフェース実装 (Interface Layer)

### ✅ タスク 5-1: API コントローラー設計

- **Goal**: REST API エンドポイントとスキーマ定義
- [x] API パス設計 (`POST /api/v1/process`, `GET /api/v1/health`)
- [x] リクエスト設計 (Multipart: file + score_threshold)
- [x] レスポンス設計（処理済み動画の R2 署名 URL, HTTP ステータス）
- [x] リクエスト/レスポンススキーマ (Pydantic) 設計
- [x] エラーレスポンス設計 (7 種類のエラーコード)
- [x] **動画時間バリデーション (3 秒〜7 分)** - 定数定義済み
- [x] **🛑 [Review] API 設計 (OpenAPI) の承認**

### ✅ タスク 5-2: Web API 実装 (TDD)

- **Goal**: FastAPI によるエンドポイント実装
- [x] **ルーター実装 (`POST /api/v1/process`)**
  - [x] ファイル一時保存 (UploadFile -> TempFile)
  - [x] 動画バリデーション (フォーマット、時間制限)
  - [x] UseCase 呼び出し + 結果変換
  - [x] ドメイン例外 -> API 例外変換
- [x] **E2E テスト（`TestClient` 使用）**
  - [x] 正常系 (短い動画ファイル)
  - [x] 異常系 (無効フォーマット、時間超過、パラメータ不正)
  - [x] 大規模動画のモックテスト
- [x] **ミドルウェア設定**
  - [x] CORS (Cloudflare Pages からのアクセス許可)
  - [x] Request Logging (処理時間、ステータス)
  - [x] ファイルサイズ制限
- [x] **依存関係の環境変数対応**
  - [x] `dependencies.py` の設定読み込みを環境変数化
- [x] **🛑 [Review] API 動作確認と E2E テスト結果**

---

## 🚀 フェーズ 6: デプロイ準備とドキュメント

### ✅ タスク 6-1: コンテナ化と構成管理

- **Goal**: 本番運用可能な Docker イメージ作成
- [x] `Dockerfile` 最適化（マルチステージビルド）
- [x] `docker-compose.yml` 整備
- [x] **🛑 [Review] コンテナビルドと動作確認** (環境依存のためスキップ: 手順書作成済み)

### ✅ タスク 6-2: ドキュメント整備

- [x] `README.md` (Backend 専用) の作成
- [x] API 仕様書 (`openapi.yaml`) のエクスポート
- [x] 開発者ガイドラインの最終更新
- [x] **🛑 [Review] 最終納品物確認**

---

## 🚀 フェーズ 7: デプロイ最適化と環境適応 (Optimization & CI/CD)

### ✅ タスク 7-1: Docker イメージ最適化

- **Goal**: イメージサイズの削減とビルド/プッシュ時間の短縮
- **現状分析 (既に実施済み):**
  - ✅ `.dockerignore`: docs/, \*.md, .git 等除外済み
  - ✅ マルチステージビルド: builder/runtime 分離済み
  - ✅ ベースイメージ: `python:3.11-slim` 使用中
  - ✅ キャッシュ最適化: requirements.txt を src より先にコピー済み
  - ❌ `tensorflow-cpu`: 依存関係エラーで不可
- **実施内容:**
  - [x] `opencv-python` → `opencv-python-headless` への切り替え
    - GUI 機能不要のため ~200MB 削減可能
    - `libgl1` 依存を削除
  - [x] BuildKit キャッシュ活用 (`--mount=type=cache,target=/root/.cache/pip`)
  - [x] 最終イメージサイズ計測および動作確認 (ユーザー側で実施)

> **Note (poetry.lock vs requirements.txt):**
> 現在の `poetry export` アプローチは、runtime イメージに poetry を含めない（~50MB 削減）ため効率的。
> キャッシュは `pyproject.toml` + `poetry.lock` のコピー時点で効いている。

### ✅ タスク 7-2: 環境適応とドキュメント更新 (Dev Env & Docs)

- **Goal**: `dev.kenken-pose-est.online` での動作保証と API 仕様の明確化
- **構成**: フロントエンド (`dev.kenken-pose-est.online`) / バックエンド (`api.kenken-pose-est.online`) は別オリジン → **CORS 必須**
- **現状分析:**
  - ✅ `main.py` に `_get_cors_origins()` で環境変数 `CORS_ORIGINS` を読み込む仕組みあり
  - ⚠️ **問題発見**: `allow_origins=["*"]` と `allow_credentials=True` の同時指定はブラウザで無効
- **実施内容:**
  - [x] CORS 設定のバグ修正
    - [x] `CORS_ORIGINS="*"` の場合は `allow_credentials=False` に自動切り替え
  - [x] 環境変数設定の確認 (`CORS_ORIGINS` は Cloud Run 側で設定が必要)
  - [x] ヘルスチェックエンドポイントの連携確認 (Cloud Run 設定は運用ガイドライン参照)
  - [x] API 仕様書 (`OpenAPI`) の更新
    - [x] バリデーションルールの明記 (動画時間: 3 秒〜7 分, ファイルサイズ: <100MB)
    - [x] エラーコードの具体的な説明を追加 (`VIDEO_TOO_SHORT` 等)
    - [x] `export_openapi.py` 再実行と `docs/openapi.yaml` 更新

### ✅ タスク 7-3: CI/CD 統合準備

- **Goal**: 自動デプロイに向けた準備 (GitHub Actions)
- [x] GitHub Actions ワークフロー (`.github/workflows/deploy.yml`) のドラフト作成
  - amd64 ネイティブビルド (ローカル M1 クロスビルドより高速)
  - `push-backend-image.sh` (または `gcloud builds submit`) のロジックを移植
  - Dev/Prod の環境分岐の仕組みを構築
- [x] 環境変数の管理 (GitHub Secrets)
  - `GCP_SA_KEY`
  - `R2_ACCESS_KEY` 等 (ワークフロー内で参照設定済み)

### ✅ タスク 7-4: 本番環境設定 & CORS 更新

- **Goal**: 本番運用に向けたアクセスポリシーの適用とデプロイフロー修正
- [x] ワークフロー (`deploy.yml`) のブランチ戦略修正
  - `develop` ブランチ -> Dev 環境
  - `main` ブランチ -> Prod 環境
- [x] CORS 設定の環境分離 (Dev/Prod)
  - 参照: `INFRA_HANDOVER.md.resolved`
  - GitHub Secrets への設定 (完了済みを確認)
- [x] **CI/CD トラブルシューティング & 修正** (追加対応)
  - Cloud Build 権限エラー (Log Streaming) の根本対策として **Docker Build (GitHub Actions Runner)** に切り替え
- [ ] Prod 環境への初回デプロイ検証 (CI 経由: ユーザー作業)

---

## 🛡️ フェーズ 8: セキュリティ強化と本番適合 (Production Readiness)

### ✅ タスク 8-1: アクセス制御の実装 (Cloudflare Access Integration)

- **Goal**: バックエンド (`*.run.app`) への直接アクセスを遮断し、Cloudflare 経由のトラフィックのみを許可する。
- [x] **バックエンド実装 (`middleware.py`)**
  - [x] `CloudflareAuthMiddleware` 追加: `X-CF-Access-Token` ヘッダー検証
  - [x] Preflight Request (`OPTIONS`) と `/health` の除外設定
  - [x] **セキュリティ強化**:
    - `secrets.compare_digest` によるタイミング攻撃対策
    - 環境変数のキャッシングによるパフォーマンス最適化
- [x] **品質保証 (Quality Assurance)**
  - [x] 単体テスト追加 (`tests/api/test_middleware.py`): カバレッジ 100% 達成
  - [x] Lint & Format 修正 (`main.py` の重複 import 削除など)
  - [x] 全体品質チェック (`check.sh`) パス (Coverage >90%)

### ⬜ タスク 8-2: インフラ連携 (Terraform)

- **Goal**: 共有シークレットの管理と環境変数注入
- [x] **Terraform 修正** (`pose-est-infra` 側で実施)
  - [x] `backend_access_token` の Secret Manager リソース定義追加
  - [x] Cloud Run への環境変数 `CLOUDFLARE_ACCESS_TOKEN` 注入設定
- [ ] `terraform apply` 実行とデプロイ (ユーザー作業)
