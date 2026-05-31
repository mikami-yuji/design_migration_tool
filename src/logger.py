"""
ログ管理モジュール

アプリケーション全体のログ設定を管理する。
ファイル出力とコンソール出力の両方に対応。
"""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path


def setup_logger(log_dir: str | None = None) -> logging.Logger:
    """
    アプリケーション用のロガーをセットアップする。

    Args:
        log_dir: ログファイルの出力ディレクトリ。Noneの場合はアプリ直下のlogs/を使用。

    Returns:
        設定済みのLoggerインスタンス
    """
    logger = logging.getLogger("pdf_migration_tool")
    logger.setLevel(logging.DEBUG)

    # 既存のハンドラがあればクリア（多重登録防止）
    if logger.handlers:
        logger.handlers.clear()

    # ログフォーマットの定義
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # コンソールハンドラ
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # ファイルハンドラ
    try:
        if log_dir is None:
            if getattr(sys, "frozen", False):
                # PyInstallerでパッケージ化されている場合
                base_dir = os.path.dirname(sys.executable)
            else:
                # 通常のスクリプト実行の場合
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            log_dir = os.path.join(base_dir, "logs")

        Path(log_dir).mkdir(parents=True, exist_ok=True)

        log_filename = f"pdf_migration_{datetime.now().strftime('%Y%m%d')}.log"
        log_filepath = os.path.join(log_dir, log_filename)

        file_handler = logging.FileHandler(log_filepath, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except OSError as e:
        logger.warning(f"ログファイルの作成に失敗しました: {e}")

    return logger


def get_logger() -> logging.Logger:
    """
    既存のロガーインスタンスを取得する。

    Returns:
        Loggerインスタンス
    """
    return logging.getLogger("pdf_migration_tool")
