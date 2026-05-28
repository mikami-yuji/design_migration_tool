"""
history_manager モジュールのテスト
"""

import os
import time
import json
from unittest.mock import patch, MagicMock

import pytest

from src.history_manager import HistoryManager, get_file_metadata
from src.logger import setup_logger

# テスト用ロガーのセットアップ
setup_logger()


@pytest.fixture
def temp_history_file(tmp_path: str) -> str:
    """テスト用の履歴ファイルパスを提供するフィクスチャ。"""
    return os.path.join(str(tmp_path), "test_history.json")


@pytest.fixture
def dummy_file(tmp_path: str) -> str:
    """テスト用のダミーファイルパスを提供するフィクスチャ。"""
    file_path = os.path.join(str(tmp_path), "dummy.pdf")
    with open(file_path, "w") as f:
        f.write("initial content")
    return file_path


class TestGetFileMetadata:
    """get_file_metadata関数のテスト"""

    def test_存在するファイルのメタデータを取得できる(self, dummy_file: str) -> None:
        """ファイルのサイズとmtimeが正しく取得できること。"""
        meta = get_file_metadata(dummy_file)
        assert meta is not None
        assert meta["size"] == len("initial content")
        assert isinstance(meta["mtime"], float)

    def test_存在しないファイルの場合はNoneを返す(self) -> None:
        """ファイルが存在しない場合はNoneが返ること。"""
        meta = get_file_metadata("nonexistent.pdf")
        assert meta is None


class TestHistoryManager:
    """HistoryManagerクラスのテスト"""

    def test_履歴ファイルがない場合空の履歴で初期化される(self, temp_history_file: str) -> None:
        """履歴ファイルが存在しない場合、正常に空の履歴で起動すること。"""
        manager = HistoryManager(temp_history_file)
        assert manager._history == {}

    def test_新規ファイルは処理対象と判定される(self, temp_history_file: str, dummy_file: str) -> None:
        """履歴にないファイルは、should_process_fileがTrueを返すこと。"""
        manager = HistoryManager(temp_history_file)
        assert manager.should_process_file(dummy_file) is True

    def test_記録後は処理対象から除外される(self, temp_history_file: str, dummy_file: str) -> None:
        """記録した後は、同じファイルはshould_process_fileがFalseを返すこと。"""
        manager = HistoryManager(temp_history_file)
        
        manager.record_processed_file(dummy_file)
        assert manager.should_process_file(dummy_file) is False

    def test_ファイルサイズが変更された場合はやり直しと判定される(
        self, temp_history_file: str, dummy_file: str
    ) -> None:
        """記録後にファイルサイズが変更された場合、should_process_fileがTrueを返すこと。"""
        manager = HistoryManager(temp_history_file)
        
        # 初期状態を記録
        manager.record_processed_file(dummy_file)
        assert manager.should_process_file(dummy_file) is False

        # ファイル内容を書き換えてサイズを変更
        with open(dummy_file, "w") as f:
            f.write("content changed and size is larger now")

        # サイズ変更検知で処理対象(True)になること
        assert manager.should_process_file(dummy_file) is True

    def test_更新日時が変更された場合はやり直しと判定される(
        self, temp_history_file: str, dummy_file: str
    ) -> None:
        """ファイルサイズが同じでも更新日時が変更された場合、should_process_fileがTrueを返すこと。"""
        manager = HistoryManager(temp_history_file)
        
        # 初期状態を記録
        manager.record_processed_file(dummy_file)
        
        # mtimeを変更するためにモックを使用（os.statの返り値を書き換える）
        original_meta = get_file_metadata(dummy_file)
        assert original_meta is not None
        
        mock_stat = MagicMock()
        mock_stat.st_size = original_meta["size"]
        mock_stat.st_mtime = original_meta["mtime"] + 10.0  # 10秒進める
        
        with patch("os.stat", return_value=mock_stat):
            # 更新日時変更検知で処理対象(True)になること
            assert manager.should_process_file(dummy_file) is True

    def test_履歴のクリアができる(self, temp_history_file: str, dummy_file: str) -> None:
        """clear_historyを呼ぶと履歴がクリアされること。"""
        manager = HistoryManager(temp_history_file)
        manager.record_processed_file(dummy_file)
        
        assert manager._history != {}
        
        manager.clear_history()
        
        assert manager._history == {}
        assert os.path.exists(temp_history_file)
        
        # クリア後は再度処理対象になること
        assert manager.should_process_file(dummy_file) is True
