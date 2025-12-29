"""一時ファイル管理クラス。

特徴:
- 自動追跡と一括クリーンアップ
- 構造化ロギング
- Context Manager サポート
"""

import contextlib
import logging
import uuid
from pathlib import Path
from types import TracebackType
from typing import Self

logger = logging.getLogger(__name__)


class TempFileManager:
    """一時ファイルを管理するクラス。

    Usage:
    ```python
    with TempFileManager() as manager:
        temp_path = manager.create_temp_path(".mp4")
        # ファイルに書き込み処理
    # スコープ終了時に自動クリーンアップ
    ```
    """

    _tracked_files: set[str]

    def __init__(self, base_dir: str | None = None) -> None:
        """初期化。

        Args:
            base_dir: 一時ファイル保存ディレクトリ。None の場合はシステム標準。
        """
        if base_dir is None:
            import tempfile

            base_dir = str(Path(tempfile.gettempdir()) / "pose-est")

        self.base_dir = Path(base_dir)
        self._tracked_files = set()
        self.base_dir.mkdir(parents=True, exist_ok=True)
        logger.debug("TempFileManager initialized: base_dir=%s", self.base_dir)

    def __enter__(self) -> Self:
        """Context Manager エントリポイント。"""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Context Manager 終了時に全ファイルをクリーンアップ。"""
        self.cleanup_all()

    def create_temp_path(self, suffix: str = ".mp4") -> str:
        """一時ファイルのパスを生成します。

        Args:
            suffix: ファイルの拡張子 (デフォルト: .mp4)

        Returns:
            生成されたファイルパス
        """
        filename = f"{uuid.uuid4()}{suffix}"
        path = self.base_dir / filename
        str_path = str(path)
        self._tracked_files.add(str_path)
        logger.debug("Created temp path: %s", str_path)
        return str_path

    def cleanup(self, file_path: str) -> bool:
        """指定されたファイルを削除します。

        Args:
            file_path: 削除対象のファイルパス

        Returns:
            削除成功時は True、ファイルが存在しないまたは失敗時は False
        """
        path = Path(file_path)
        deleted = False

        if path.exists():
            with contextlib.suppress(OSError):
                path.unlink()
                deleted = True
                logger.debug("Deleted temp file: %s", file_path)

        if not deleted and path.exists():
            logger.warning("Failed to delete temp file: %s", file_path)

        if file_path in self._tracked_files:
            self._tracked_files.remove(file_path)

        return deleted

    def cleanup_all(self) -> int:
        """管理しているすべての一時ファイルを削除します。

        Returns:
            削除されたファイル数
        """
        count = 0
        for path in list(self._tracked_files):
            if self.cleanup(path):
                count += 1

        logger.info("Cleaned up %d temp files", count)
        return count

    @property
    def tracked_count(self) -> int:
        """現在追跡中のファイル数。"""
        return len(self._tracked_files)
