"""
main.py の PDFMigrationApp クラスのテスト
"""

import os
from unittest.mock import MagicMock, patch
import pytest

from main import PDFMigrationApp


class TestPDFMigrationApp:
    """PDFMigrationApp クラスのテスト"""

    @patch("main.show_copy_confirmation")
    @patch("main.copy_file")
    def test_新しいファイルが検知されたときに正常に処理とコピーを行う(
        self,
        mock_copy_file: MagicMock,
        mock_show_confirmation: MagicMock,
    ) -> None:
        """検知されたファイルが正常に処理され、コピーされること。"""
        # アプリケーションのセットアップと設定のモック化
        app = PDFMigrationApp()
        app._config = {
            "watch_folder": "C:\\watch",
            "destination_folder": "C:\\dest",
            "file_extensions": [".pdf"],
        }

        # 履歴管理とポップアップの挙動のモック化
        app._history = MagicMock()
        app._history.should_process_file.return_value = True
        mock_show_confirmation.return_value = True
        mock_copy_file.return_value = "C:\\dest\\test.pdf"

        # テスト実行
        test_file = "C:\\watch\\test.pdf"
        app._on_new_file_detected(test_file)

        # 検証
        app._history.should_process_file.assert_called_once_with(test_file)
        mock_show_confirmation.assert_called_once_with(test_file, "C:\\dest")
        mock_copy_file.assert_called_once_with(test_file, "C:\\dest")
        app._history.record_processed_file.assert_called_once_with(test_file)

    @patch("main.show_copy_confirmation")
    @patch("main.copy_file")
    def test_ユーザーがキャンセルした場合はコピーを行わない(
        self,
        mock_copy_file: MagicMock,
        mock_show_confirmation: MagicMock,
    ) -> None:
        """ユーザーがキャンセルした場合、コピーがスキップされ履歴のみ記録されること。"""
        app = PDFMigrationApp()
        app._config = {
            "watch_folder": "C:\\watch",
            "destination_folder": "C:\\dest",
            "file_extensions": [".pdf"],
        }

        app._history = MagicMock()
        app._history.should_process_file.return_value = True
        mock_show_confirmation.return_value = False

        test_file = "C:\\watch\\test.pdf"
        app._on_new_file_detected(test_file)

        # 検証
        app._history.should_process_file.assert_called_once_with(test_file)
        mock_show_confirmation.assert_called_once_with(test_file, "C:\\dest")
        mock_copy_file.assert_not_called()
        app._history.record_processed_file.assert_called_once_with(test_file)
