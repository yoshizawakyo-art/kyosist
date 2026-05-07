"""
cli_executor.py のテストモジュール
"""

import pytest

from cli_executor import CLIExecutor


@pytest.mark.asyncio
async def test_cli_execute_git_status():
    """git status コマンドを実行"""
    executor = CLIExecutor()
    result = await executor.execute("git status")

    assert result["status"] in ["success", "error"]
    assert result["command"] == "git status"
    assert "exit_code" in result
    assert "duration_ms" in result


@pytest.mark.asyncio
async def test_cli_execute_echo():
    """echo コマンドを実行（シンプルテスト）"""
    executor = CLIExecutor()
    # echo は許可されていないため、エラーが返される
    result = await executor.execute("echo hello")

    assert result["status"] == "error"
    assert "未許可のコマンド" in result["stderr"]


@pytest.mark.asyncio
async def test_cli_execute_python():
    """python コマンドを実行"""
    executor = CLIExecutor()
    result = await executor.execute("python -c \"print('hello')\"")

    assert result["status"] == "success"
    assert result["exit_code"] == 0
    assert "hello" in result["stdout"]


@pytest.mark.asyncio
async def test_cli_execute_ruff_check():
    """ruff check コマンドを実行"""
    executor = CLIExecutor()
    result = await executor.execute("ruff check .")

    # ruff がインストールされていない場合は失敗するが、許可チェックは通る
    assert result["command"] == "ruff check ."
    assert "exit_code" in result


@pytest.mark.asyncio
async def test_cli_disallowed_command():
    """許可されていないコマンドはエラーを返す"""
    executor = CLIExecutor()
    result = await executor.execute("rm -rf /")

    assert result["status"] == "error"
    assert "未許可のコマンド" in result["stderr"]
    assert result["exit_code"] == 1


@pytest.mark.asyncio
async def test_cli_disallowed_argument():
    """許可されていない引数はエラーを返す"""
    executor = CLIExecutor()
    result = await executor.execute("git clone https://example.com/repo.git")

    assert result["status"] == "error"
    assert "未許可の引数" in result["stderr"]


@pytest.mark.asyncio
async def test_cli_empty_command():
    """空のコマンドはエラーを返す"""
    executor = CLIExecutor()
    result = await executor.execute("")

    assert result["status"] == "error"
    assert "コマンドが指定されていません" in result["stderr"]


@pytest.mark.asyncio
async def test_cli_timeout():
    """タイムアウトをテスト（sleep コマンドは許可されていないため、スキップ）"""
    executor = CLIExecutor()
    # sleep は許可されていないため、代わりにパス検証のみ確認
    result = await executor.execute("sleep 100")

    assert result["status"] == "error"
    assert "未許可のコマンド" in result["stderr"]


@pytest.mark.asyncio
async def test_cli_allowed_commands():
    """許可されたコマンドのリスト確認"""
    executor = CLIExecutor()

    # npm run build は許可される
    allowed, error = executor._is_command_allowed("npm run build")
    assert allowed is True
    assert error == ""

    # git status は許可される
    allowed, error = executor._is_command_allowed("git status")
    assert allowed is True
    assert error == ""

    # python は許可される
    allowed, error = executor._is_command_allowed("python script.py")
    assert allowed is True
    assert error == ""


@pytest.mark.asyncio
async def test_cli_disallowed_npm_command():
    """許可されていない npm コマンド"""
    executor = CLIExecutor()
    result = await executor.execute("npm uninstall package")

    assert result["status"] == "error"
    assert "未許可の引数" in result["stderr"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
