# ストレージ容量のメンテナンスガイド

開発を進める中でストレージ容量が圧迫された際に、原因の特定と解消を行うためのガイドラインです。
特に **Docker (Colima)**, **Python (Poetry)**, **Terraform**, **Node.js (npm)** のキャッシュが肥大化しやすい傾向にあります。

## 1. 現状の確認と原因の考察

まずはどこで容量が消費されているかを確認します。

### 考察のポイント
- **Docker (Colima):** コンテナイメージを頻繁にビルド・プルしていると、未使用のイメージやレイヤーが蓄積します。`~/.colima` が数十GB規模になることは珍しくありません。
- **Poetry:** 複数のプロジェクトで仮想環境を作成したり、ライブラリのバージョンアップを繰り返すと、ダウンロードキャッシュが肥大化します。
- **Terraform:** `terraform init` を実行するたびに、各プロジェクト・各環境ごとにプロバイダ（AWS/GCP/Cloudflare等のプラグイン）がダウンロードされるため、重複して容量を消費します。
- **npm:** 頻繁には肥大化しませんが、キャッシュが残ることがあります。また、プロジェクトごとの `node_modules` が巨大になることがあります。

### 確認コマンド

ターミナルで以下を実行して確認してください。

```bash
# 1. Docker (Colima) の使用量 (macOS標準パス)
du -sh ~/.colima

# (Colima起動時のみ) Docker内部の詳細確認
docker system df

# 2. Poetry キャッシュサイズ
du -sh ~/Library/Caches/pypoetry

# 3. npm キャッシュサイズ
du -sh ~/.npm

# 4. Terraform キャッシュサイズ (プロジェクト内)
find . -name ".terraform" -type d -exec du -sh {} +

# 5. 現在のディレクトリ配下で容量を食っているものを探す (上位20件)
du -h -d 2 . | sort -h | tail -n 20
```

---

## 2. 削除・クリーンアップ手順

不要なデータを削除して容量を確保します。
**注意:** 削除すると、次回実行時に再ダウンロードやビルドが必要になるため、一時的に時間がかかる場合があります。

### Docker / Colima
最も容量を圧迫しやすい箇所です。

```bash
# パターンA: 未使用のコンテナ・イメージ・ボリュームのみ削除 (Colima起動中に実行)
docker system prune -a --volumes

# パターンB: Colimaインスタンスをリセット (最も効果的・データは全て消えます)
# データベースの中身なども消えるため、開発環境を初期化したい場合に推奨
colima delete --force
# 再開時は colima start

# パターンC: Colimaの設定・キャッシュを完全に削除 (究極のリセット)
# インスタンスを削除しても ~/.colima の容量が解放されない場合に有効です
rm -rf ~/.colima
# 注意: 次回 `colima start` 時に OSイメージ (ISO) の再ダウンロードが発生します
```

### Poetry (Backend)
ライブラリのダウンロードキャッシュを削除します。

```bash
# ディレクトリを直接削除 (確実)
rm -rf ~/Library/Caches/pypoetry

# またはコマンドで (Poetryがインストールされている場合)
poetry cache clear --all pypi
```

### Terraform (Infra)
プロジェクト内の `.terraform` ディレクトリ（プロバイダバイナリ等）を削除します。次回 `terraform init` で再生成されます。

```bash
find . -name ".terraform" -type d -exec rm -rf {} +
```

### npm (Frontend)
npmのキャッシュをクリアします。

```bash
npm cache clean --force
```

---

## 3. その他の有益な情報・運用設定

### Colima のディスクサイズ制限
Colimaはデフォルトで大きめのディスクサイズを確保することがあります。
起動時にディスクサイズを明示的に指定することで、無制限な肥大化を防げます（ただし、足りなくなるとエラーになります）。

```bash
# 例: ディスクサイズを 30GB に制限して起動
colima start --disk 30
```

### Docker の自動クリーンアップ
定期的に `prune` を行うことで、肥大化を防げます。

```bash
# 停止しているコンテナ、タグのないイメージなどを削除
docker system prune
```

### Node.js (node_modules)
プロジェクト内の `node_modules` も大きくなりがちです。おかしな挙動をする場合や容量を減らしたい場合は、再インストールを行ってください。

```bash
# node_modules を削除して再インストール
rm -rf node_modules
npm ci
```
