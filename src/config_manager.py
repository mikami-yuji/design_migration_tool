"""
設定管理モジュール

config.jsonの読み込み・保存・バリデーションを行う。
初回起動時のデフォルト設定生成にも対応。
"""

import json
import os
import sys
from pathlib import Path
from typing import Any

from src.logger import get_logger

# デフォルト設定値
DEFAULT_CONFIG: dict[str, Any] = {
    "watch_folder": "",
    "destination_folder": "",
    "file_extensions": [".pdf"],
    "check_interval": 1.0,
    "show_notification_on_move": True,
    "run_on_startup": True,
}


def _get_base_dir() -> str:
    """
    アプリケーションのベースディレクトリを取得する。

    Returns:
        実行ファイルまたはスクリプトの配置ディレクトリパス
    """
    if getattr(sys, "frozen", False):
        # PyInstallerでパッケージ化されている場合
        return os.path.dirname(sys.executable)
    # 通常のスクリプト実行の場合
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# 設定ファイルのパス（プロジェクトルート直下）
CONFIG_FILE_PATH: str = os.path.join(_get_base_dir(), "config.json")


def load_config(config_path: str | None = None) -> dict[str, Any]:
    """
    設定ファイルを読み込む。

    Args:
        config_path: 設定ファイルのパス。Noneの場合はデフォルトパスを使用。

    Returns:
        設定内容の辞書

    Raises:
        json.JSONDecodeError: JSONのパースに失敗した場合
    """
    logger = get_logger()
    path = config_path or CONFIG_FILE_PATH

    if not os.path.exists(path):
        # 親ディレクトリ（プロジェクトルートなど）に config.json があればそこから設定を引き継ぐ
        parent_config_path = os.path.join(
            os.path.dirname(os.path.dirname(path)), "config.json"
        )
        if os.path.exists(parent_config_path):
            logger.info(f"親ディレクトリの設定ファイルから引き継ぎます: {parent_config_path}")
            try:
                import shutil
                shutil.copy2(parent_config_path, path)
            except OSError as e:
                logger.warning(f"設定ファイルの引き継ぎコピーに失敗しました: {e}")

        # コピー成否を再チェック
        if not os.path.exists(path):
            logger.info(f"設定ファイルが見つかりません: {path}")
            return DEFAULT_CONFIG.copy()

    try:
        with open(path, "r", encoding="utf-8") as f:
            config = json.load(f)

        # デフォルト値でマージ（未設定項目を補完）
        merged_config = DEFAULT_CONFIG.copy()
        merged_config.update(config)

        logger.info(f"設定ファイルを読み込みました: {path}")
        return merged_config

    except json.JSONDecodeError as e:
        logger.error(f"設定ファイルのパースに失敗しました: {e}")
        raise
    except OSError as e:
        logger.error(f"設定ファイルの読み込みに失敗しました: {e}")
        return DEFAULT_CONFIG.copy()


def save_config(config: dict[str, Any], config_path: str | None = None) -> bool:
    """
    設定内容をファイルに保存する。

    Args:
        config: 保存する設定内容の辞書
        config_path: 保存先のパス。Noneの場合はデフォルトパスを使用。

    Returns:
        保存成功ならTrue、失敗ならFalse
    """
    logger = get_logger()
    path = config_path or CONFIG_FILE_PATH

    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

        logger.info(f"設定ファイルを保存しました: {path}")
        return True

    except OSError as e:
        logger.error(f"設定ファイルの保存に失敗しました: {e}")
        return False


def validate_config(config: dict[str, Any]) -> list[str]:
    """
    設定内容をバリデーションする。

    Args:
        config: バリデーション対象の設定辞書

    Returns:
        エラーメッセージのリスト（空リストならバリデーション成功）
    """
    errors: list[str] = []

    # 監視フォルダのチェック
    watch_folder = config.get("watch_folder", "")
    if not watch_folder:
        errors.append("監視フォルダが設定されていません。")
    elif not os.path.isdir(watch_folder):
        errors.append(f"監視フォルダが存在しません: {watch_folder}")

    # 移動先フォルダのチェック
    destination_folder = config.get("destination_folder", "")
    if not destination_folder:
        errors.append("移動先フォルダが設定されていません。")
    elif not os.path.isdir(destination_folder):
        # 移動先フォルダは自動作成を試みる
        try:
            Path(destination_folder).mkdir(parents=True, exist_ok=True)
        except OSError:
            errors.append(f"移動先フォルダを作成できません: {destination_folder}")

    # 監視対象拡張子のチェック
    extensions = config.get("file_extensions", [])
    if not extensions or not isinstance(extensions, list):
        errors.append("監視対象の拡張子が設定されていません。")

    # 監視間隔のチェック
    interval = config.get("check_interval", 0)
    if not isinstance(interval, (int, float)) or interval <= 0:
        errors.append("監視間隔は正の数値で指定してください。")

    return errors


def is_first_launch(config_path: str | None = None) -> bool:
    """
    初回起動かどうかを判定する。

    Args:
        config_path: 設定ファイルのパス。

    Returns:
        設定ファイルが存在しないか、フォルダが未設定ならTrue
    """
    path = config_path or CONFIG_FILE_PATH

    if not os.path.exists(path):
        return True

    try:
        config = load_config(path)
        return not config.get("watch_folder") or not config.get("destination_folder")
    except Exception:
        return True
