from collections.abc import Generator
from unittest.mock import MagicMock, patch

import pytest

from posture_estimation.domain.exceptions import StorageError
from posture_estimation.infrastructure.storage.r2_service import R2StorageService


@pytest.fixture
def mock_boto3() -> Generator[MagicMock, None, None]:
    """boto3.client のモックフィクスチャ。"""
    with patch("boto3.client") as mock:
        yield mock

def test_initialization(mock_boto3: MagicMock) -> None:
    """R2StorageService の初期化 (boto3 client 作成) を確認する。"""
    R2StorageService("http://r2/endpoint", "key", "secret", "my-bucket")
    mock_boto3.assert_called_once_with(
        "s3",
        endpoint_url="http://r2/endpoint",
        aws_access_key_id="key",
        aws_secret_access_key="secret"  # noqa: S106
    )

def test_upload(mock_boto3: MagicMock) -> None:
    """Upload メソッドが正常にファイルをアップロードするか確認する。"""
    service = R2StorageService("url", "key", "secret", "bucket")
    mock_client = mock_boto3.return_value

    key = service.upload("/local/file.mp4", "remote/file.mp4")

    mock_client.upload_file.assert_called_once_with("/local/file.mp4", "bucket", "remote/file.mp4")
    assert key == "remote/file.mp4"

def test_upload_failure(mock_boto3: MagicMock) -> None:
    """アップロード失敗時に StorageError を送出するか確認する。"""
    service = R2StorageService("url", "key", "secret", "bucket")
    mock_client = mock_boto3.return_value
    mock_client.upload_file.side_effect = Exception("S3 error")

    with pytest.raises(StorageError, match="Upload failed"):
        service.upload("file", "key")

def test_generate_signed_url(mock_boto3: MagicMock) -> None:
    """generate_signed_url が正常に署名付き URL を生成するか確認する。"""
    service = R2StorageService("url", "key", "secret", "bucket")
    mock_client = mock_boto3.return_value
    mock_client.generate_presigned_url.return_value = "http://signed/url"

    url = service.generate_signed_url("remote/file.mp4", expires_in=120)

    mock_client.generate_presigned_url.assert_called_once_with(
        "get_object",
        Params={"Bucket": "bucket", "Key": "remote/file.mp4"},
        ExpiresIn=120
    )
    assert url == "http://signed/url"
