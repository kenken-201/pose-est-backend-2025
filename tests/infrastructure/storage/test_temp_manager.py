from pathlib import Path

import pytest

from posture_estimation.infrastructure.storage.temp_manager import TempFileManager


@pytest.fixture
def temp_dir(tmp_path: Path) -> str:
    """一時ディレクトリのパスを提供するフィクスチャ。"""
    return str(tmp_path)


def test_create_and_cleanup(temp_dir: str) -> None:
    """一時ファイルの作成と個別の削除 (cleanup) を確認する。"""
    manager = TempFileManager(base_dir=temp_dir)

    # Create
    file_path = manager.create_temp_path(suffix=".mp4")
    assert file_path.startswith(temp_dir)
    assert file_path.endswith(".mp4")

    # Simulate file creation
    # Simulate file creation
    with Path(file_path).open("w") as f:
        f.write("dummy")

    assert Path(file_path).exists()

    # Cleanup single file (just remove from tracking in this implementation, or actually delete?)
    # The requirement is "automatic cleanup".
    # Implementation detail: cleanup(file_path) should remove file
    manager.cleanup(file_path)
    assert not Path(file_path).exists()


def test_cleanup_all(temp_dir: str) -> None:
    """cleanup_all で管理下の全ファイルが削除されるか確認する。"""
    manager = TempFileManager(base_dir=temp_dir)

    p1 = manager.create_temp_path()
    p2 = manager.create_temp_path()

    with Path(p1).open("w") as f:
        f.write("1")
    with Path(p2).open("w") as f:
        f.write("2")

    manager.cleanup_all()
    assert not Path(p1).exists()
    assert not Path(p2).exists()
