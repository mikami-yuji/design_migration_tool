"""
ファイルコピーモジュール

PDFファイルを指定フォルダへ安全にコピーする（元のファイルは残す）。
同名ファイルが存在する場合のリネーム処理にも対応。
"""

import os
import shutil
from pathlib import Path

from src.logger import get_logger


def generate_unique_filename(destination_folder: str, filename: str) -> str:
    """
    同名ファイルが存在する場合、ユニークなファイル名を生成する。

    「ファイル名_1.pdf」「ファイル名_2.pdf」のように連番を付与する。

    Args:
        destination_folder: コピー先フォルダのパス
        filename: 元のファイル名

    Returns:
        ユニークなファイル名
    """
    destination_path = os.path.join(destination_folder, filename)

    if not os.path.exists(destination_path):
        return filename

    # 拡張子とファイル名を分離
    name, ext = os.path.splitext(filename)
    counter = 1

    while True:
        new_filename = f"{name}_{counter}{ext}"
        new_path = os.path.join(destination_folder, new_filename)
        if not os.path.exists(new_path):
            return new_filename
        counter += 1


def copy_file(source_path: str, destination_folder: str) -> str | None:
    """
    ファイルを指定フォルダにコピーする（元のファイルは残す）。

    Args:
        source_path: コピー元のファイルパス
        destination_folder: コピー先フォルダのパス

    Returns:
        コピー先のファイルパス。失敗した場合はNone。
    """
    logger = get_logger()

    try:
        # コピー元ファイルの存在確認
        if not os.path.isfile(source_path):
            logger.error(f"コピー元ファイルが見つかりません: {source_path}")
            return None

        # コピー先フォルダの存在確認・作成
        Path(destination_folder).mkdir(parents=True, exist_ok=True)

        # ユニークなファイル名を生成
        filename = os.path.basename(source_path)
        unique_filename = generate_unique_filename(destination_folder, filename)
        destination_path = os.path.join(destination_folder, unique_filename)

        # ファイルコピー実行（メタデータ保持コピー）
        shutil.copy2(source_path, destination_path)

        logger.info(f"ファイルをコピーしました: {source_path} → {destination_path}")
        return destination_path

    except PermissionError as e:
        logger.error(f"ファイルのコピー権限がありません: {e}")
        return None
    except OSError as e:
        logger.error(f"ファイルのコピーに失敗しました: {e}")
        return None



def is_file_ready(file_path: str) -> bool:
    """
    ファイルが書き込み完了しているか確認する。

    他のプロセスがファイルを書き込み中でないことを、
    排他ロックを試みることで判定する。

    Args:
        file_path: チェック対象のファイルパス

    Returns:
        ファイルが利用可能ならTrue
    """
    try:
        # ファイルを排他モードで開けるかチェック
        with open(file_path, "rb+"):
            return True
    except (PermissionError, OSError):
        return False
