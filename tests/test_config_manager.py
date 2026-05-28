"""
config_manager モジュールのテスト
"""

import json
import os
import tempfile

import pytest

from src.config_manager import (
    DEFAULT_CONFIG,
    is_first_launch,
    load_config,
    save_config,
    validate_config,
)
from src.logger import setup_logger

# テスト用のロガーを初期化
setup_logger()


class TestLoadConfig:
    """load_config関数のテスト"""

    def test_存在しないファイルの場合デフォルト設定を返す(self, tmp_path: str) -> None:
        """設定ファイルが存在しない場合、デフォルト設定が返される。"""
        config_path = os.path.join(str(tmp_path), "nonexistent.json")
        config = load_config(config_path)
        assert config == DEFAULT_CONFIG

    def test_正常な設定ファイルを読み込む(self, tmp_path: str) -> None:
        """有効なJSONファイルから設定を正しく読み込めること。"""
        config_path = os.path.join(str(tmp_path), "config.json")
        test_config = {
            "watch_folder": "C:\\test\\watch",
            "destination_folder": "C:\\test\\dest",
        }
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(test_config, f)

        config = load_config(config_path)

        assert config["watch_folder"] == "C:\\test\\watch"
        assert config["destination_folder"] == "C:\\test\\dest"
        # デフォルト値がマージされていること
        assert config["file_extensions"] == [".pdf"]
        assert config["check_interval"] == 1.0

    def test_不正なJSONファイルの場合例外を発生させる(self, tmp_path: str) -> None:
        """不正なJSONファイルの場合、JSONDecodeErrorが発生すること。"""
        config_path = os.path.join(str(tmp_path), "bad_config.json")
        with open(config_path, "w", encoding="utf-8") as f:
            f.write("{ invalid json }")

        with pytest.raises(json.JSONDecodeError):
            load_config(config_path)


class TestSaveConfig:
    """save_config関数のテスト"""

    def test_設定ファイルを正常に保存できる(self, tmp_path: str) -> None:
        """設定辞書をJSONファイルとして正しく保存できること。"""
        config_path = os.path.join(str(tmp_path), "config.json")
        test_config = {
            "watch_folder": "C:\\test\\watch",
            "destination_folder": "C:\\test\\dest",
        }

        result = save_config(test_config, config_path)

        assert result is True
        assert os.path.exists(config_path)

        # 保存内容の検証
        with open(config_path, "r", encoding="utf-8") as f:
            saved = json.load(f)
        assert saved == test_config

    def test_日本語パスを正しく保存できる(self, tmp_path: str) -> None:
        """日本語を含むパスがensure_ascii=Falseで正しく保存されること。"""
        config_path = os.path.join(str(tmp_path), "config.json")
        test_config = {
            "watch_folder": "C:\\ドキュメント\\監視フォルダ",
            "destination_folder": "C:\\ドキュメント\\移動先",
        }

        save_config(test_config, config_path)

        with open(config_path, "r", encoding="utf-8") as f:
            content = f.read()
        # ensure_ascii=Falseで保存されているため、日本語がそのまま含まれる
        assert "監視フォルダ" in content


class TestValidateConfig:
    """validate_config関数のテスト"""

    def test_フォルダ未設定の場合エラーを返す(self) -> None:
        """監視フォルダ・移動先フォルダが空の場合、エラーメッセージが返ること。"""
        config = {"watch_folder": "", "destination_folder": ""}
        errors = validate_config(config)
        assert len(errors) >= 2
        assert any("監視フォルダ" in e for e in errors)
        assert any("移動先フォルダ" in e for e in errors)

    def test_存在しない監視フォルダの場合エラーを返す(self) -> None:
        """存在しない監視フォルダパスの場合、エラーメッセージが返ること。"""
        config = {
            "watch_folder": "C:\\nonexistent\\folder",
            "destination_folder": "",
            "file_extensions": [".pdf"],
            "check_interval": 1.0,
        }
        errors = validate_config(config)
        assert any("存在しません" in e for e in errors)

    def test_拡張子が未設定の場合エラーを返す(self) -> None:
        """file_extensionsが空の場合、エラーメッセージが返ること。"""
        config = {
            "watch_folder": tempfile.gettempdir(),
            "destination_folder": tempfile.gettempdir(),
            "file_extensions": [],
            "check_interval": 1.0,
        }
        errors = validate_config(config)
        assert any("拡張子" in e for e in errors)

    def test_監視間隔が不正な場合エラーを返す(self) -> None:
        """check_intervalが0以下の場合、エラーメッセージが返ること。"""
        config = {
            "watch_folder": tempfile.gettempdir(),
            "destination_folder": tempfile.gettempdir(),
            "file_extensions": [".pdf"],
            "check_interval": -1,
        }
        errors = validate_config(config)
        assert any("監視間隔" in e for e in errors)

    def test_正常な設定の場合空リストを返す(self, tmp_path: str) -> None:
        """全ての値が正常な場合、エラーリストが空であること。"""
        watch_dir = os.path.join(str(tmp_path), "watch")
        dest_dir = os.path.join(str(tmp_path), "dest")
        os.makedirs(watch_dir, exist_ok=True)

        config = {
            "watch_folder": watch_dir,
            "destination_folder": dest_dir,
            "file_extensions": [".pdf"],
            "check_interval": 1.0,
        }
        errors = validate_config(config)
        assert errors == []


class TestIsFirstLaunch:
    """is_first_launch関数のテスト"""

    def test_設定ファイルが存在しない場合Trueを返す(self, tmp_path: str) -> None:
        """設定ファイルがない場合は初回起動と判定すること。"""
        config_path = os.path.join(str(tmp_path), "nonexistent.json")
        assert is_first_launch(config_path) is True

    def test_フォルダが未設定の場合Trueを返す(self, tmp_path: str) -> None:
        """フォルダが空文字の場合は初回起動と判定すること。"""
        config_path = os.path.join(str(tmp_path), "config.json")
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump({"watch_folder": "", "destination_folder": ""}, f)
        assert is_first_launch(config_path) is True

    def test_設定済みの場合Falseを返す(self, tmp_path: str) -> None:
        """フォルダが設定済みの場合は初回起動ではないと判定すること。"""
        config_path = os.path.join(str(tmp_path), "config.json")
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "watch_folder": "C:\\test",
                    "destination_folder": "C:\\test\\dest",
                },
                f,
            )
        assert is_first_launch(config_path) is False
