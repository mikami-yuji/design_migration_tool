"""
フォルダ監視モジュール

watchdogを使用して指定フォルダのPDFファイル生成を監視する。
新しいPDFを検知したらコールバック関数を呼び出す。
"""

import os
import time
from typing import Callable

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from src.file_mover import is_file_ready
from src.logger import get_logger



class PDFFileHandler(FileSystemEventHandler):
    """
    PDFファイルの作成・移動イベントを処理するハンドラ。

    新しいPDFファイルが監視フォルダに追加されたことを検知し、
    指定のコールバック関数を呼び出す。
    """

    def __init__(
        self,
        watch_folder: str,
        file_extensions: list[str],
        on_new_file: Callable[[str], None],
    ) -> None:
        """
        Args:
            watch_folder: 監視するフォルダパス
            file_extensions: 監視対象のファイル拡張子リスト（例: [".pdf"]）
            on_new_file: 新しいファイルが検知されたときに呼び出されるコールバック
        """
        super().__init__()
        self._watch_folder = os.path.normpath(os.path.abspath(watch_folder))
        self._file_extensions = [ext.lower() for ext in file_extensions]
        self._on_new_file = on_new_file
        self._logger = get_logger()

    def _is_target_file(self, file_path: str) -> bool:
        """対象のファイル拡張子かどうかを判定する。"""
        return any(file_path.lower().endswith(ext) for ext in self._file_extensions)

    def on_created(self, event: FileSystemEvent) -> None:
        """ファイル作成イベントのハンドラ。"""
        if event.is_directory:
            return

        file_path = str(event.src_path)

        if not self._is_target_file(file_path):
            return

        self._logger.info(f"新しいファイルを検知しました: {file_path}")

        # ファイルの書き込み完了を待機（最大30秒）
        self._wait_for_file_ready(file_path)

        self._on_new_file(file_path)

    def on_moved(self, event: FileSystemEvent) -> None:
        """ファイル移動イベントのハンドラ（リネーム含む）。"""
        if event.is_directory:
            return

        dest_path = str(event.dest_path)

        # 移動先が監視フォルダ直下であるか検証（監視フォルダ外への移動イベントを無視するため）
        abs_dest = os.path.normpath(os.path.abspath(dest_path))
        if os.path.dirname(abs_dest) != self._watch_folder:
            self._logger.debug(
                f"監視フォルダ外への移動イベントのため無視します: {dest_path}"
            )
            return

        if not self._is_target_file(dest_path):
            return

        self._logger.info(f"ファイルの移動/リネームを検知しました: {dest_path}")

        self._wait_for_file_ready(dest_path)

        self._on_new_file(dest_path)

    def _wait_for_file_ready(self, file_path: str, timeout: int = 30) -> None:
        """
        ファイルの書き込みが完了するまで待機する。

        ファイルサイズと最終更新日時 (mtime) を定期的にチェックし、
        変化しなくなるまで（書き込みが完了するまで）待機する。

        Args:
            file_path: 待機対象のファイルパス
            timeout: 最大待機時間（秒）
        """
        elapsed = 0.0
        interval = 0.5
        
        last_size = -1
        last_mtime = -1
        
        # 安定状態が何回連続して続いたら完了とみなすか (2回 = 1.0秒間安定)
        stable_count = 0
        required_stable = 2

        while elapsed < timeout:
            try:
                if not os.path.exists(file_path):
                    time.sleep(interval)
                    elapsed += interval
                    continue
                
                stat = os.stat(file_path)
                current_size = stat.st_size
                current_mtime = stat.st_mtime
                
                # 前回チェック時とサイズ・更新日時が一致しているか確認
                if current_size == last_size and current_mtime == last_mtime:
                    # 0バイト以上のファイルが安定した時のみOKとする
                    if current_size > 0:
                        stable_count += 1
                        if stable_count >= required_stable:
                            # 念のため、排他ロックが取得できるかも併せて確認
                            if is_file_ready(file_path):
                                self._logger.debug(f"ファイル書き込みの安定と完了を確認: {file_path}")
                                return
                    else:
                        stable_count = 0
                else:
                    stable_count = 0
                    
                last_size = current_size
                last_mtime = current_mtime
                
            except OSError:
                stable_count = 0
                
            time.sleep(interval)
            elapsed += interval

        self._logger.warning(
            f"ファイルの書き込み完了待機がタイムアウトしました: {file_path}"
        )



class FileWatcher:
    """
    フォルダ監視を管理するクラス。

    watchdogのObserverをラップし、監視の開始・停止を制御する。
    """

    def __init__(
        self,
        watch_folder: str,
        file_extensions: list[str],
        on_new_file: Callable[[str], None],
    ) -> None:
        """
        Args:
            watch_folder: 監視するフォルダパス
            file_extensions: 監視対象のファイル拡張子リスト
            on_new_file: 新しいファイル検知時のコールバック
        """
        self._watch_folder = watch_folder
        self._handler = PDFFileHandler(watch_folder, file_extensions, on_new_file)
        self._observer: Observer | None = None
        self._logger = get_logger()

    def start(self) -> None:
        """フォルダ監視を開始する。"""
        if self._observer is not None and self._observer.is_alive():
            self._logger.warning("監視は既に実行中です。")
            return

        self._observer = Observer()
        self._observer.schedule(
            self._handler,
            self._watch_folder,
            recursive=False,
        )
        self._observer.start()
        self._logger.info(f"フォルダ監視を開始しました: {self._watch_folder}")

    def stop(self) -> None:
        """フォルダ監視を停止する。"""
        if self._observer is not None and self._observer.is_alive():
            self._observer.stop()
            self._observer.join(timeout=5)
            self._logger.info("フォルダ監視を停止しました。")

        self._observer = None

    @property
    def is_running(self) -> bool:
        """監視が実行中かどうかを返す。"""
        return self._observer is not None and self._observer.is_alive()
