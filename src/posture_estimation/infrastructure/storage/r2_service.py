import boto3
from botocore.exceptions import ClientError

from posture_estimation.domain.exceptions import StorageError
from posture_estimation.domain.interfaces import IStorageService


class R2StorageService(IStorageService):
    """Cloudflare R2 (S3互換) を使用したストレージサービス。"""

    def __init__(
        self, endpoint_url: str, access_key: str, secret_key: str, bucket_name: str
    ) -> None:
        """初期化。

        Args:
            endpoint_url (str): R2 API エンドポイント
            access_key (str): AWS Access Key ID
            secret_key (str): AWS Secret Access Key
            bucket_name (str): バケット名
        """
        self.bucket_name = bucket_name
        try:
            self.s3_client = boto3.client(
                "s3",
                endpoint_url=endpoint_url,
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
            )
        except Exception as e:
            msg = f"Failed to initialize R2 client: {e}"
            raise StorageError(msg) from e

    def upload(self, file_path: str, key: str) -> str:
        """ファイルをアップロードします。

        Args:
            file_path (str): ファイルパス
            key (str): 保存キー

        Returns:
            str: キー
        """
        try:
            self.s3_client.upload_file(file_path, self.bucket_name, key)
            return key
        except (ClientError, Exception) as e:
            msg = f"Upload failed for {key}: {e}"
            raise StorageError(msg) from e

    def generate_signed_url(self, key: str, expires_in: int = 3600) -> str:
        """署名付き URL を生成します。

        Args:
            key (str): キー
            expires_in (int): 有効期限(秒)

        Returns:
            str: 署名付き URL
        """
        try:
            url: str = self.s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": key},
                ExpiresIn=expires_in,
            )
            return url
        except (ClientError, Exception) as e:
            msg = f"Failed to generate signed URL for {key}: {e}"
            raise StorageError(msg) from e
