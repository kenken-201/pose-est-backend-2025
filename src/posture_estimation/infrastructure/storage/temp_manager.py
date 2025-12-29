import contextlib
import uuid
from pathlib import Path


class TempFileManager:
    """一時ファイルを管理するクラス。"""

    # 生成したファイルのパスを保持するリスト
    _tracked_files: set[str]

    def __init__(self, base_dir: str | None = None) -> None:
        """初期化。

        Args:
            base_dir (str | None): 一時ファイルを保存するディレクトリ。Noneの場合はシステム標準の一時領域を使用。
        """
        if base_dir is None:
            import tempfile
            base_dir = str(Path(tempfile.gettempdir()) / "pose-est")

        self.base_dir = Path(base_dir)
        self._tracked_files = set()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def create_temp_path(self, suffix: str = ".mp4") -> str:
        """一時ファイルのパスを生成します。

        Args:
            suffix (str): ファイルの拡張子

        Returns:
            str: 生成されたファイルパス
        """
        filename = f"{uuid.uuid4()}{suffix}"
        path = self.base_dir / filename
        str_path = str(path)
        self._tracked_files.add(str_path)
        return str_path

    def cleanup(self, file_path: str) -> None:
        """指定されたファイルを削除します。

        Args:
            file_path (str): 削除対象のファイルパス
        """
        with contextlib.suppress(OSError):
            Path(file_path).unlink()  # 削除失敗時は無視(ログ出力推奨だが今回は省略)

        if file_path in self._tracked_files:
            self._tracked_files.remove(file_path)

    def cleanup_all(self) -> None:
        """管理しているすべての一時ファイルを削除します。"""
        # コピーを作成してループ (削除中にset変更エラーを防ぐ)
        for path in list(self._tracked_files):
            self.cleanup(path)
