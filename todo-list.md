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

### ⬜ タスク 2-2: ドメイン層の実装 (TDD)

- **Goal**: 純粋な Python コードによるドメインロジック実装
- [ ] 値オブジェクトとエンティティの実装と単体テスト
- [ ] `typing.Protocol` を使用したインターフェース定義
- [ ] ドメイン例外の定義
- [ ] **🛑 [Review] ドメイン実装と型安全性の確認**

---

## 🧠 フェーズ 3: コア機能・インフラ実装 (Infrastructure Layer)

### ⬜ タスク 3-1: インフラストラクチャ設計

- **Goal**: 外部システム（ML モデル, OpenCV, Storage）との連携設計
- [ ] MoveNet モデルのラッパー設計（シングルトン、ロード戦略）
- [ ] OpenCV 動画処理クラスの設計
- [ ] ローカルストレージ管理の設計
- [ ] **🛑 [Review] インフラ設計の承認**

### ⬜ タスク 3-2: ML エンジンと動画処理の実装 (TDD)

- **Goal**: MoveNet と OpenCV の統合
- [ ] `MoveNetPoseEstimator` の実装とモックテスト
- [ ] `VideoProcessor` (OpenCV) の実装と実ファイルテスト
- [ ] **🛑 [Review] 姿勢推定精度の確認（動画出力確認）**

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
