"""
file_mover モジュールのテスト
"""

import os

import pytest

from src.file_mover import copy_file, generate_unique_filename, is_file_ready
from src.logger import setup_logger

# テスト用のロガーを初期化
setup_logger()


class TestGenerateUniqueFilename:
    """generate_unique_filename関数のテスト"""

    def test_同名ファイルがない場合元のファイル名を返す(self, tmp_path: str) -> None:
        """コピー先に同名ファイルがない場合、元のファイル名がそのまま返ること。"""
        result = generate_unique_filename(str(tmp_path), "test.pdf")
        assert result == "test.pdf"

    def test_同名ファイルがある場合連番付きファイル名を返す(self, tmp_path: str) -> None:
        """コピー先に同名ファイルがある場合、_1付きのファイル名が返ること。"""
        # 同名ファイルを作成
        existing = os.path.join(str(tmp_path), "test.pdf")
        with open(existing, "w") as f:
            f.write("dummy")

        result = generate_unique_filename(str(tmp_path), "test.pdf")
        assert result == "test_1.pdf"

    def test_複数の同名ファイルがある場合正しい連番を返す(self, tmp_path: str) -> None:
        """_1, _2 が存在する場合、_3 が返ること。"""
        for name in ["test.pdf", "test_1.pdf", "test_2.pdf"]:
            with open(os.path.join(str(tmp_path), name), "w") as f:
                f.write("dummy")

        result = generate_unique_filename(str(tmp_path), "test.pdf")
        assert result == "test_3.pdf"


class TestCopyFile:
    """copy_file関数のテスト"""

    def test_ファイルを正常にコピーできる(self, tmp_path: str) -> None:
        """ファイルが正しくコピー先に複製され、コピー元も残ること。"""
        # コピー元ファイルを作成
        source_dir = os.path.join(str(tmp_path), "source")
        dest_dir = os.path.join(str(tmp_path), "dest")
        os.makedirs(source_dir)

        source_file = os.path.join(source_dir, "test.pdf")
        with open(source_file, "w") as f:
            f.write("PDF content")

        result = copy_file(source_file, dest_dir)

        assert result is not None
        assert os.path.exists(result)
        # コピーなので元のファイルも残っていること
        assert os.path.exists(source_file)

    def test_コピー先フォルダが自動作成される(self, tmp_path: str) -> None:
        """コピー先フォルダが存在しない場合、自動的に作成されること。"""
        source_file = os.path.join(str(tmp_path), "test.pdf")
        with open(source_file, "w") as f:
            f.write("PDF content")

        dest_dir = os.path.join(str(tmp_path), "new", "nested", "folder")
        result = copy_file(source_file, dest_dir)

        assert result is not None
        assert os.path.isdir(dest_dir)

    def test_存在しないコピー元ファイルの場合Noneを返す(self, tmp_path: str) -> None:
        """コピー元ファイルが存在しない場合、Noneが返ること。"""
        result = copy_file(
            os.path.join(str(tmp_path), "nonexistent.pdf"),
            str(tmp_path),
        )
        assert result is None

    def test_同名ファイルがある場合リネームしてコピーする(self, tmp_path: str) -> None:
        """コピー先に同名ファイルが存在する場合、_1を付与してコピーすること。"""
        source_dir = os.path.join(str(tmp_path), "source")
        dest_dir = os.path.join(str(tmp_path), "dest")
        os.makedirs(source_dir)
        os.makedirs(dest_dir)

        # コピー先に既存ファイルを配置
        existing = os.path.join(dest_dir, "test.pdf")
        with open(existing, "w") as f:
            f.write("existing")

        # コピー元ファイルを作成
        source_file = os.path.join(source_dir, "test.pdf")
        with open(source_file, "w") as f:
            f.write("new content")

        result = copy_file(source_file, dest_dir)

        assert result is not None
        assert result.endswith("test_1.pdf")
        assert os.path.exists(result)
        # 元の既存ファイルも残っていること
        assert os.path.exists(existing)
        # コピーなので元ファイルも残っていること
        assert os.path.exists(source_file)



class TestIsFileReady:
    """is_file_ready関数のテスト"""

    def test_通常のファイルの場合Trueを返す(self, tmp_path: str) -> None:
        """ロックされていないファイルの場合、Trueが返ること。"""
        file_path = os.path.join(str(tmp_path), "test.pdf")
        with open(file_path, "w") as f:
            f.write("content")

        assert is_file_ready(file_path) is True

    def test_存在しないファイルの場合Falseを返す(self, tmp_path: str) -> None:
        """存在しないファイルの場合、Falseが返ること。"""
        file_path = os.path.join(str(tmp_path), "nonexistent.pdf")
        assert is_file_ready(file_path) is False
