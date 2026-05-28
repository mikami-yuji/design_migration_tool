"""
履歴管理モジュール

処理済みファイルの履歴を記録・管理する。
ファイル名に加えて、ファイルサイズと最終更新日時(mtime)を記録し、
二重ポップアップの防止と、やり直し出力(上書き再出力)の検知を両立する。
"""

import json
import os
from typing import Any

from src.logger import get_logger

# 履歴ファイルの保存先パス（プロジェクトルート直下）
HISTORY_FILE_PATH: str = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "history.json"
)


def get_file_metadata(file_path: str) -> dict[str, Any] | None:
    """
    指定ファイルのメタデータ（サイズと最終更新日時）を取得する。

    Args:
        file_path: 対象ファイルのパス

    Returns:
        メタデータの辞書（取得失敗時はNone）
    """
    logger = get_logger()
    try:
        if not os.path.isfile(file_path):
            return None

        stat = os.stat(file_path)
        # Round the mtime to 2 decimal places to bypass JSON float precision discrepancies
        return {
            "size": stat.st_size,
            "mtime": round(stat.st_mtime, 2),
        }
    except OSError as e:
        logger.error(f"ファイルのメタデータ取得に失敗しました ({file_path}): {e}")
        return None


class HistoryManager:
    """
    処理済みファイルの履歴を永続化・管理するクラス。
    """

    def __init__(self, history_path: str | None = None) -> None:
        """
        Args:
            history_path: 履歴ファイルの保存先パス。Noneの場合はデフォルトパスを使用。
        """
        self._history_path = history_path or HISTORY_FILE_PATH
        self._history: dict[str, dict[str, Any]] = {}
        self._logger = get_logger()
        self.load_history()

    def load_history(self) -> None:
        """履歴ファイルを読み込む。"""
        if not os.path.exists(self._history_path):
            self._history = {}
            return

        try:
            with open(self._history_path, "r", encoding="utf-8") as f:
                self._history = json.load(f)
            self._logger.info(f"履歴ファイルを読み込みました: {self._history_path}")
        except json.JSONDecodeError as e:
            self._logger.error(f"履歴ファイルのパースに失敗しました、新規作成します: {e}")
            self._history = {}
        except OSError as e:
            self._logger.error(f"履歴ファイルの読み込みに失敗しました: {e}")
            self._history = {}

    def save_history(self) -> bool:
        """現在の履歴をファイルに保存する。"""
        try:
            with open(self._history_path, "w", encoding="utf-8") as f:
                json.dump(self._history, f, ensure_ascii=False, indent=2)
            return True
        except OSError as e:
            self._logger.error(f"履歴ファイルの保存に失敗しました: {e}")
            return False

    def should_process_file(self, file_path: str) -> bool:
        """
        指定ファイルを処理（ポップアップ確認）すべきかどうか判定する。

        以下のいずれかに該当する場合は処理対象(True)とする。
        1. 履歴に存在しない
        2. 履歴に存在するが、ファイルサイズが異なる
        3. 履歴に存在するが、最終更新日時(mtime)が異なる（やり直し出力）

        Args:
            file_path: 判定対象ファイルのパス

        Returns:
            処理すべきならTrue、スキップすべきならFalse
        """
        current_meta = get_file_metadata(file_path)
        if current_meta is None:
            # メタデータが取得できない（アクセス不可など）ファイルは処理しない
            return False

        filename = os.path.basename(file_path)

        # 履歴に存在しない場合は新規ファイルとみなす
        if filename not in self._history:
            self._logger.debug(f"履歴なし (新規ファイル): {filename}")
            return True

        saved_meta = self._history[filename]

        # サイズまたは更新日時が異なれば、上書きによるやり直しデータとみなす
        size_changed = saved_meta.get("size") != current_meta["size"]
        mtime_changed = saved_meta.get("mtime") != current_meta["mtime"]

        if size_changed or mtime_changed:
            self._logger.info(
                f"変更を検知 (やり直しデータ): {filename} "
                f"(サイズ変更: {size_changed}, 時間変更: {mtime_changed})"
            )
            return True

        # 完全一致する場合は処理済みなのでスキップ
        self._logger.debug(f"処理スキップ (完全一致): {filename}")
        return False

    def record_processed_file(self, file_path: str) -> None:
        """
        ファイルを処理済みとして履歴に記録・保存する。

        Args:
            file_path: 記録対象ファイルのパス
        """
        current_meta = get_file_metadata(file_path)
        if current_meta is None:
            return

        filename = os.path.basename(file_path)
        self._history[filename] = current_meta
        self.save_history()
        self._logger.debug(f"履歴に記録しました: {filename} ({current_meta})")

    def clear_history(self) -> None:
        """履歴を完全に消去する。"""
        self._history = {}
        self.save_history()
        self._logger.info("履歴をクリアしました。")
