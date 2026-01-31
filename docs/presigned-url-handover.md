# 署名付き URL アップロード機能 - バックエンド引継書

## 📋 概要

Cloud Run の HTTP/1.1 リクエストボディサイズ制限（32MB 固定）を回避するため、大容量動画ファイル（〜100MB+）を Cloudflare R2 に直接アップロードする機能を実装します。

## 🏗️ アーキテクチャ変更

### Before (現状)

```
[Browser] ---(multipart/form-data: video file)---> [Cloud Run]
                                                      ↓
                                              動画処理 + R2 保存
```

**問題**: Cloud Run の HTTP/1.1 制限で 32MB 以上のリクエストが `413 Content Too Large` で拒否される。

### After (変更後)

```
[Browser] ---(1. POST /upload/initiate)---> [Cloud Run] ---(署名付きURL生成)
    ↓
[Browser] <---(upload_url, object_key)---
    ↓
[Browser] ---(2. PUT: 動画ファイル)---> [R2 Storage]
    ↓
[Browser] ---(3. POST /process: object_key)---> [Cloud Run]
                                                   ↓
                                           R2からダウンロード → 処理 → R2保存
```

**メリット**:

- ファイルサイズ制限の回避（R2 の上限は 5GB）
- Cloud Run の負荷軽減
- アップロード遅延の改善

---

## 🔧 実装タスク

### タスク 9-1: 署名付き URL 生成ロジック

**ファイル**: `src/posture_estimation/infrastructure/r2_service.py`

```python
def generate_presigned_upload_url(
    self,
    object_key: str,
    content_type: str = "video/mp4",
    expires_in: int = 900,  # 15分
) -> str:
    """
    R2 への PUT アップロード用署名付き URL を生成します。

    Args:
        object_key: アップロード先のオブジェクトキー (例: "uploads/uuid.mp4")
        content_type: Content-Type (video/* のみ許可)
        expires_in: 有効期限（秒）

    Returns:
        署名付き URL (PUT 専用)
    """
    return self._client.generate_presigned_url(
        ClientMethod="put_object",
        Params={
            "Bucket": self._bucket_name,
            "Key": object_key,
            "ContentType": content_type,
        },
        ExpiresIn=expires_in,
    )
```

**注意点**:

- 既存の `signature_version='s3v4'` 設定を流用（SigV4 必須）
- `ContentType` パラメータを必ず含める（ブラウザからの PUT リクエストと一致させる）

---

### タスク 9-2: アップロード開始エンドポイント

**ファイル**: `src/posture_estimation/api/routes.py`

```python
@router.post("/upload/initiate", response_model=UploadInitiateResponse)
async def initiate_upload(
    request: UploadInitiateRequest,
    storage: R2StorageService = Depends(get_storage_service),
) -> UploadInitiateResponse:
    """
    動画アップロード用の署名付き URL を発行します。

    クライアントはこの URL を使用して R2 に直接アップロードします。
    """
    # UUID ベースのオブジェクトキー生成
    object_key = f"uploads/{uuid.uuid4()}{Path(request.filename).suffix}"

    # Content-Type バリデーション
    if not request.content_type.startswith("video/"):
        raise HTTPException(
            status_code=400,
            detail={"error": {"code": "INVALID_FILE_TYPE", "message": "動画ファイルのみ対応"}},
        )

    # ファイルサイズバリデーション (例: 500MB 上限)
    if request.file_size > 500 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail={"error": {"code": "FILE_TOO_LARGE", "message": "ファイルサイズ上限: 500MB"}},
        )

    upload_url = storage.generate_presigned_upload_url(
        object_key=object_key,
        content_type=request.content_type,
    )

    return UploadInitiateResponse(
        upload_url=upload_url,
        object_key=object_key,
        expires_in=900,
    )
```

**スキーマ** (`api/schemas.py`):

```python
class UploadInitiateRequest(BaseModel):
    filename: str
    content_type: str
    file_size: int  # bytes

class UploadInitiateResponse(BaseModel):
    upload_url: str
    object_key: str
    expires_in: int  # seconds
```

---

### タスク 9-3: 処理エンドポイントの変更

**ファイル**: `src/posture_estimation/api/routes.py`

現在の `/process` エンドポイントを object_key ベースに変更します。

```python
class ProcessByKeyRequest(BaseModel):
    object_key: str
    score_threshold: float = 0.3

@router.post("/process", response_model=VideoProcessResponse)
async def process_video(
    request: ProcessByKeyRequest = None,
    file: UploadFile = File(None),  # 後方互換用（オプション）
    storage: R2StorageService = Depends(get_storage_service),
    use_case: ProcessVideoUseCase = Depends(get_use_case),
) -> VideoProcessResponse:
    """
    動画を処理し、姿勢推定結果を描画した動画を返します。

    object_key が指定された場合は R2 からダウンロードして処理します。
    file が指定された場合は従来どおり multipart/form-data として処理します。
    """
    if request and request.object_key:
        # R2 からダウンロード
        local_path = storage.download_to_temp(request.object_key)
        # ... 処理
    elif file:
        # 従来の multipart 処理（後方互換）
        # ...
    else:
        raise HTTPException(status_code=400, detail="object_key or file required")
```

**追加メソッド** (`r2_service.py`):

```python
def download_to_temp(self, object_key: str) -> Path:
    """
    R2 からファイルをダウンロードし、一時ファイルパスを返します。
    """
    suffix = Path(object_key).suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as f:
        self._client.download_fileobj(self._bucket_name, object_key, f)
        return Path(f.name)
```

---

## 🔒 セキュリティ考慮事項

1. **署名付き URL の特性**
   - PUT メソッド専用（GET/DELETE は不可）
   - 有効期限: 15分
   - オブジェクトキーは UUID ベースで推測不可能

2. **Content-Type 検証**
   - `video/*` のみ許可
   - アップロード時とリクエスト時の Content-Type が一致しないと R2 が拒否

3. **ファイルサイズ上限**
   - `/upload/initiate` でサイズ検証（例: 500MB）
   - R2 側の上限は 5GB

---

## 🧪 テスト観点

1. **単体テスト**
   - 署名付き URL 生成の正常系
   - 不正な Content-Type での拒否
   - ファイルサイズ超過での拒否

2. **統合テスト**
   - `/upload/initiate` → R2 PUT → `/process` のフロー
   - object_key が存在しない場合のエラーハンドリング

3. **E2E テスト**
   - Dev 環境でのブラウザからの動作確認
   - 80MB+ のファイルでの動作確認

---

## 📚 参考リンク

- [boto3 generate_presigned_url](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html#S3.Client.generate_presigned_url)
- [Cloudflare R2 S3 互換性](https://developers.cloudflare.com/r2/api/s3/api/)
- [Cloud Run リクエスト制限](https://cloud.google.com/run/docs/configuring/request-timeout)
