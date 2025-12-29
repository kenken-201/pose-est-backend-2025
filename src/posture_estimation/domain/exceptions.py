class DomainError(Exception):
    """ドメイン層で発生する例外の基底クラス。

    Attributes:
        message (str): エラーメッセージ
    """

    def __init__(self, message: str = "A domain error occurred") -> None:
        """初期化メソッド。

        Args:
            message (str): エラーの詳細メッセージ
        """
        self.message = message
        super().__init__(self.message)


class VideoProcessingError(DomainError):
    """動画処理(読み込み、書き込み、解析)に失敗した場合の例外。"""

    def __init__(self, message: str = "Video processing failed") -> None:
        """初期化メソッド。"""
        super().__init__(message)


class PoseEstimationError(DomainError):
    """姿勢推定処理に失敗した場合の例外。"""

    def __init__(self, message: str = "Pose estimation failed") -> None:
        """初期化メソッド。"""
        super().__init__(message)


class StorageError(DomainError):
    """ストレージ操作(保存、アップロード、URL生成)に失敗した場合の例外。"""

    def __init__(self, message: str = "Storage operation failed") -> None:
        """初期化メソッド。"""
        super().__init__(message)
