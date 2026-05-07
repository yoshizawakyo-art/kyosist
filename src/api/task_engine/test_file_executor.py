"""
file_executor.py のテストモジュール
"""

import pytest
import tempfile
from pathlib import Path

from api.task_engine.file_executor import FileExecutor


@pytest.fixture
def temp_dir():
    """テスト用の一時ディレクトリを生成"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.mark.asyncio
async def test_file_create(temp_dir):
    """ファイル作成をテスト"""
    executor = FileExecutor()
    # 許可されるパスに設定
    executor.ALLOWED_PREFIX = temp_dir

    file_path = str(temp_dir / "test.txt")
    result = await executor.create(file_path, "Hello World")

    assert result["status"] == "success"
    assert result["action"] == "create"
    assert Path(file_path).exists()
    assert Path(file_path).read_text() == "Hello World"


@pytest.mark.asyncio
async def test_file_edit(temp_dir):
    """ファイル編集をテスト"""
    executor = FileExecutor()
    executor.ALLOWED_PREFIX = temp_dir

    file_path = str(temp_dir / "test.txt")
    # ファイルを先に作成
    await executor.create(file_path, "Original")

    result = await executor.edit(file_path, "Updated")

    assert result["status"] == "success"
    assert result["action"] == "edit"
    assert Path(file_path).read_text() == "Updated"


@pytest.mark.asyncio
async def test_file_delete(temp_dir):
    """ファイル削除をテスト"""
    executor = FileExecutor()
    executor.ALLOWED_PREFIX = temp_dir

    file_path = str(temp_dir / "test.txt")
    # ファイルを先に作成
    await executor.create(file_path, "Content")

    result = await executor.delete(file_path)

    assert result["status"] == "success"
    assert result["action"] == "delete"
    assert not Path(file_path).exists()


@pytest.mark.asyncio
async def test_file_read(temp_dir):
    """ファイル読み込みをテスト"""
    executor = FileExecutor()
    executor.ALLOWED_PREFIX = temp_dir

    file_path = str(temp_dir / "test.txt")
    content = "Test Content"
    # ファイルを先に作成
    await executor.create(file_path, content)

    result = await executor.read(file_path)

    assert result["status"] == "success"
    assert result["action"] == "read"
    assert result["content"] == content


@pytest.mark.asyncio
async def test_file_create_missing_path(temp_dir):
    """パスなしの作成はエラーを返す"""
    executor = FileExecutor()
    executor.ALLOWED_PREFIX = temp_dir

    result = await executor.create("", "Content")

    assert result["status"] == "error"
    assert "パスが指定されていません" in result["message"]


@pytest.mark.asyncio
async def test_file_path_traversal_attack(temp_dir):
    """.. パストラバーサルを検出"""
    executor = FileExecutor()
    executor.ALLOWED_PREFIX = temp_dir

    result = await executor.create("../../../etc/passwd", "Malicious")

    assert result["status"] == "error"
    assert "相対パス（..）は許可されていません" in result["message"]


@pytest.mark.asyncio
async def test_file_path_outside_root(temp_dir):
    """許可されたルート外のパスはエラー"""
    executor = FileExecutor()
    executor.ALLOWED_PREFIX = temp_dir

    result = await executor.create("/etc/passwd", "Malicious")

    assert result["status"] == "error"
    assert "プロジェクトルート外" in result["message"]


@pytest.mark.asyncio
async def test_file_edit_nonexistent():
    """存在しないファイルの編集はエラーを返す"""
    executor = FileExecutor()

    result = await executor.edit(
        str(Path(executor.ALLOWED_PREFIX) / "nonexistent.txt"), "Content"
    )

    assert result["status"] == "error"
    assert "ファイルが存在しません" in result["message"]


@pytest.mark.asyncio
async def test_file_delete_nonexistent():
    """存在しないファイルの削除はエラーを返す"""
    executor = FileExecutor()

    result = await executor.delete(
        str(Path(executor.ALLOWED_PREFIX) / "nonexistent.txt")
    )

    assert result["status"] == "error"
    assert "ファイルが存在しません" in result["message"]


@pytest.mark.asyncio
async def test_file_read_nonexistent():
    """存在しないファイルの読み込みはエラーを返す"""
    executor = FileExecutor()

    result = await executor.read(str(Path(executor.ALLOWED_PREFIX) / "nonexistent.txt"))

    assert result["status"] == "error"
    assert "ファイルが存在しません" in result["message"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
