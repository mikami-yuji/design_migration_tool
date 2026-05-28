"""
file_watcher モジュールのテスト
"""

import os
import time
import threading

import pytest

from src.file_watcher import FileWatcher, PDFFileHandler
from src.logger import setup_logger

# テスト用のロガーを初期化
setup_logger()


class TestPDFFileHandler:
    """PDFFileHandlerクラスのテスト"""

    def test_PDF拡張子を対象ファイルとして判定する(self) -> None:
        """'.pdf'拡張子のファイルがターゲットとして判定されること。"""
        handler = PDFFileHandler(".", [".pdf"], lambda x: None)
        assert handler._is_target_file("test.pdf") is True
        assert handler._is_target_file("TEST.PDF") is True

    def test_非対象の拡張子を除外する(self) -> None:
        """'.txt'などの非対象拡張子が除外されること。"""
        handler = PDFFileHandler(".", [".pdf"], lambda x: None)
        assert handler._is_target_file("test.txt") is False
        assert handler._is_target_file("test.docx") is False

    def test_複数の拡張子を監視できる(self) -> None:
        """複数の拡張子がターゲットとして正しく判定されること。"""
        handler = PDFFileHandler(".", [".pdf", ".xlsx"], lambda x: None)
        assert handler._is_target_file("test.pdf") is True
        assert handler._is_target_file("test.xlsx") is True
        assert handler._is_target_file("test.doc") is False


class TestFileWatcher:
    """FileWatcherクラスのテスト"""

    def test_監視を開始できる(self, tmp_path: str) -> None:
        """watcherが正常に起動できること。"""
        watcher = FileWatcher(str(tmp_path), [".pdf"], lambda x: None)
        watcher.start()

        assert watcher.is_running is True

        watcher.stop()
        assert watcher.is_running is False

    def test_監視を停止できる(self, tmp_path: str) -> None:
        """watcherが正常に停止できること。"""
        watcher = FileWatcher(str(tmp_path), [".pdf"], lambda x: None)
        watcher.start()
        watcher.stop()

        assert watcher.is_running is False

    def test_新しいPDFファイルを検知する(self, tmp_path: str) -> None:
        """監視フォルダにPDFファイルが追加された際にコールバックが呼ばれること。"""
        detected_files: list[str] = []
        event = threading.Event()

        def on_new_file(file_path: str) -> None:
            detected_files.append(file_path)
            event.set()

        watcher = FileWatcher(str(tmp_path), [".pdf"], on_new_file)
        watcher.start()

        try:
            # テスト用PDFファイルを作成
            time.sleep(0.5)  # watchdogの初期化を待機
            test_file = os.path.join(str(tmp_path), "test_document.pdf")
            with open(test_file, "w") as f:
                f.write("PDF content")

            # コールバックが呼ばれるまで最大10秒待機
            event.wait(timeout=10)

            assert len(detected_files) >= 1
            assert any("test_document.pdf" in f for f in detected_files)
        finally:
            watcher.stop()

    def test_非対象ファイルは検知しない(self, tmp_path: str) -> None:
        """非対象拡張子のファイルではコールバックが呼ばれないこと。"""
        detected_files: list[str] = []

        watcher = FileWatcher(
            str(tmp_path),
            [".pdf"],
            lambda x: detected_files.append(x),
        )
        watcher.start()

        try:
            time.sleep(0.5)
            # 非対象のファイルを作成
            test_file = os.path.join(str(tmp_path), "test.txt")
            with open(test_file, "w") as f:
                f.write("text content")

            time.sleep(2)
            assert len(detected_files) == 0
        finally:
            watcher.stop()
