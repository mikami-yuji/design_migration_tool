"""
startup_manager モジュールのテスト
"""

import os
from unittest.mock import MagicMock, patch
import pytest

from src.startup_manager import (
    get_startup_folder,
    get_shortcut_path,
    is_startup_registered,
    create_startup_shortcut,
    remove_startup_shortcut,
    SHORTCUT_NAME,
)


class TestStartupManager:
    """startup_manager の機能テスト"""

    def test_get_startup_folder(self) -> None:
        """スタートアップフォルダのパスが正しく取得できること。"""
        folder = get_startup_folder()
        assert folder.endswith(r"Microsoft\Windows\Start Menu\Programs\Startup")

    def test_get_shortcut_path(self) -> None:
        """ショートカットパスに指定のファイル名が含まれていること。"""
        path = get_shortcut_path()
        assert path.endswith(SHORTCUT_NAME)

    @patch("src.startup_manager.get_shortcut_path")
    @patch("os.path.exists")
    def test_is_startup_registered(self, mock_exists: MagicMock, mock_get_path: MagicMock) -> None:
        """登録状態の判定テスト。"""
        mock_get_path.return_value = r"C:\fake\Startup\test.lnk"
        mock_exists.return_value = True
        assert is_startup_registered() is True

        mock_exists.return_value = False
        assert is_startup_registered() is False

    @patch("subprocess.run")
    @patch("os.makedirs")
    def test_create_startup_shortcut(self, mock_makedirs: MagicMock, mock_subproc: MagicMock) -> None:
        """ショートカット作成コマンドが呼ばれること。"""
        mock_subproc.return_value = MagicMock(returncode=0)
        assert create_startup_shortcut() is True
        mock_subproc.assert_called_once()

    @patch("os.path.exists")
    @patch("os.remove")
    def test_remove_startup_shortcut(self, mock_remove: MagicMock, mock_exists: MagicMock) -> None:
        """ショートカット削除が正しく実行されること。"""
        mock_exists.return_value = True
        assert remove_startup_shortcut() is True
        mock_remove.assert_called_once()
