"""Cloudflare R2 (S3互換) を使用したストレージサービス。

特徴:
- 自動リトライ (adaptive mode, max 3 attempts)
- 署名付き URL 生成
- 詳細なエラーハンドリング
"""

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from posture_estimation.domain.exceptions import StorageError
from posture_estimation.domain.interfaces import IStorageService


class R2StorageService(IStorageService):
    """Cloudflare R2 (S3互換) を使用したストレージサービス。

    Features:
    - Automatic retry with exponential backoff (adaptive mode)
    - Connection timeout and read timeout configuration
    - Presigned URL generation for secure access
    """

    # リトライ設定
    _DEFAULT_MAX_ATTEMPTS = 3
    _DEFAULT_CONNECT_TIMEOUT = 10
    _DEFAULT_READ_TIMEOUT = 30

    def __init__(
        self,
        endpoint_url: str,
        access_key: str,
        secret_key: str,
        bucket_name: str,
        max_attempts: int = _DEFAULT_MAX_ATTEMPTS,
    ) -> None:
        """初期化。

        Args:
            endpoint_url: R2 API エンドポイント
            access_key: AWS Access Key ID
            secret_key: AWS Secret Access Key
            bucket_name: バケット名
            max_attempts: 最大リトライ回数 (デフォルト: 3)

        Raises:
            StorageError: クライアント初期化に失敗した場合
        """
        self.bucket_name = bucket_name
        try:
            # リトライとタイムアウトの設定
            config = Config(
                retries={
                    "max_attempts": max_attempts,
                    "mode": "adaptive",  # 自動指数バックオフ
                },
                connect_timeout=self._DEFAULT_CONNECT_TIMEOUT,
                read_timeout=self._DEFAULT_READ_TIMEOUT,
            )

            self.s3_client = boto3.client(
                "s3",
                endpoint_url=endpoint_url,
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                config=config,
            )
        except Exception as e:
            msg = f"Failed to initialize R2 client: {e}"
            raise StorageError(msg) from e

    def upload(self, file_path: str, key: str) -> str:
        """ファイルをアップロードします。

        Args:
            file_path: ローカルファイルパス
            key: 保存キー (S3 オブジェクトキー)

        Returns:
            アップロードされたキー

        Raises:
            StorageError: アップロードに失敗した場合
        """
        try:
            self.s3_client.upload_file(file_path, self.bucket_name, key)
            return key
        except (ClientError, OSError) as e:
            msg = f"Upload failed for {key}: {e}"
            raise StorageError(msg) from e

    def generate_signed_url(self, key: str, expires_in: int = 3600) -> str:
        """署名付き URL を生成します。

        Args:
            key: 対象のキー
            expires_in: 有効期限 (秒, デフォルト: 1時間)

        Returns:
            署名付き URL

        Raises:
            StorageError: URL 生成に失敗した場合
        """
        try:
            url: str = self.s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": key},
                ExpiresIn=expires_in,
            )
            return url
        except ClientError as e:
            msg = f"Failed to generate signed URL for {key}: {e}"
            raise StorageError(msg) from e
