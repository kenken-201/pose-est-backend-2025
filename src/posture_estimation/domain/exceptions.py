class DomainError(Exception):
    """ドメイン層で発生する例外の基底クラス。"""


class VideoProcessingError(DomainError):
    """動画処理(読み込み、書き込み、解析)に失敗した場合の例外。"""


class PoseEstimationError(DomainError):
    """姿勢推定処理に失敗した場合の例外。"""


class StorageError(DomainError):
    """ストレージ操作(保存、アップロード、URL生成)に失敗した場合の例外。"""
