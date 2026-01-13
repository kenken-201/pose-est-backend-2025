"""TempFileManager のテスト。

テストケース:
- 一時ファイル作成と個別削除
- 一括削除
- Context Manager
- 存在しないファイルの削除
- tracked_count プロパティ
"""

from pathlib import Path

import pytest

from posture_estimation.infrastructure.storage.temp_manager import TempFileManager


@pytest.fixture
def temp_dir(tmp_path: Path) -> str:
    """一時ディレクトリのパスを提供するフィクスチャ。"""
    return str(tmp_path)


def test_create_and_cleanup(temp_dir: str) -> None:
    """一時ファイルの作成と個別の削除を確認する。"""
    manager = TempFileManager(base_dir=temp_dir)

    file_path = manager.create_temp_path(suffix=".mp4")
    assert file_path.startswith(temp_dir)
    assert file_path.endswith(".mp4")
    assert manager.tracked_count == 1

    # ファイル作成
    Path(file_path).write_text("dummy")
    assert Path(file_path).exists()

    # cleanup で削除
    result = manager.cleanup(file_path)
    assert result is True
    assert not Path(file_path).exists()
    assert manager.tracked_count == 0


def test_cleanup_all(temp_dir: str) -> None:
    """cleanup_all で管理下の全ファイルが削除されるか確認する。"""
    manager = TempFileManager(base_dir=temp_dir)

    p1 = manager.create_temp_path()
    p2 = manager.create_temp_path()

    Path(p1).write_text("1")
    Path(p2).write_text("2")

    count = manager.cleanup_all()
    assert count == 2
    assert not Path(p1).exists()
    assert not Path(p2).exists()
    assert manager.tracked_count == 0


def test_context_manager(temp_dir: str) -> None:
    """Context Manager として使用した際にファイルがクリーンアップされるか確認する。"""
    with TempFileManager(base_dir=temp_dir) as manager:
        p1 = manager.create_temp_path()
        Path(p1).write_text("test")
        assert Path(p1).exists()

    # スコープ終了後にファイルが削除されていること
    assert not Path(p1).exists()


def test_cleanup_nonexistent_file(temp_dir: str) -> None:
    """存在しないファイルの削除が False を返すことを確認する。"""
    manager = TempFileManager(base_dir=temp_dir)

    # 追跡対象に追加後、ファイルを作成せずに削除
    fake_path = manager.create_temp_path()
    result = manager.cleanup(fake_path)

    assert result is False
    assert manager.tracked_count == 0


def test_default_base_dir() -> None:
    """base_dir 未指定時にシステム一時ディレクトリが使用されるか確認する。"""
    import tempfile

    manager = TempFileManager()
    expected_base = Path(tempfile.gettempdir()) / "pose-est"

    assert manager.base_dir == expected_base
