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
- [x] `VideoProcessor` 実装（音声保持・結合ロジック）
  - [x] Source/Sink 実装 (OpenCV)
  - [x] Audio Merger 実装 (FFmpeg)
- [x] `R2StorageService` 実装（アップロード・URL 発行）
- [x] **🛑 [Review] 姿勢推定精度と音声保持・R2 保存の確認**

---

## 🔧 フェーズ 4: アプリケーション・統合 (Application Layer)

### ⬜ タスク 4-1: ユースケース設計

- **Goal**: アプリケーションの振る舞い（処理フロー）の定義
- [ ] `ProcessVideoUseCase` のフロー設計（エラーハンドリング、トランザクション）
- [ ] DI（依存性注入）コンテナの構成設計
- [ ] **🛑 [Review] ユースケース設計の承認**

### ⬜ タスク 4-2: アプリケーションサービス実装 (TDD)

- **Goal**: ドメインとインフラをつなぐ実装
- [ ] `ProcessVideoUseCase` の実装と統合テスト
- [ ] DI コンテナ (`dependency-injector`) の実装
- [ ] **🛑 [Review] アプリケーションロジックの確認**

---

## 🔌 フェーズ 5: API インターフェース実装 (Interface Layer)

### ⬜ タスク 5-1: API コントローラー設計

- **Goal**: REST API エンドポイントとスキーマ定義
- [ ] API パス設計 (`POST /api/v1/process`)
- [ ] レスポンス設計（処理済み動画の R2 署名 URL, HTTP ステータス）
- [ ] リクエスト/レスポンススキーマ (Pydantic) 設計
- [ ] エラーレスポンス設計
- [ ] **🛑 [Review] API 設計 (OpenAPI) の承認**

### ⬜ タスク 5-2: Web API 実装 (TDD)

- **Goal**: FastAPI によるエンドポイント実装
- [ ] ルーター実装
- [ ] E2E テスト（`TestClient` 使用）
- [ ] ミドルウェア（CORS, Logging）設定
- [ ] **🛑 [Review] API 動作確認と E2E テスト結果**

---

## 🚀 フェーズ 6: デプロイ準備とドキュメント

### ⬜ タスク 6-1: コンテナ化と構成管理

- **Goal**: 本番運用可能な Docker イメージ作成
- [ ] `Dockerfile` 最適化（マルチステージビルド）
- [ ] `docker-compose.yml` 整備
- [ ] **🛑 [Review] コンテナビルドと動作確認**

### ⬜ タスク 6-2: ドキュメント整備

- [ ] `README.md` (Backend 専用) の作成
- [ ] API 仕様書 (`openapi.yaml`) のエクスポート
- [ ] 開発者ガイドラインの最終更新
- [ ] **🛑 [Review] 最終納品物確認**
