"""
デザイン依頼書データフォルダ移行ツール - メインエントリーポイント

システムから生成されたPDFファイルを検知し、
ポップアップで確認後に指定フォルダへ自動移動するツール。

使い方:
    python main.py
"""

import os
import sys
import threading
import time

from src.config_manager import (
    is_first_launch,
    load_config,
    save_config,
    validate_config,
)
from src.file_mover import copy_file
from src.file_watcher import FileWatcher
from src.history_manager import HistoryManager
from src.logger import get_logger, setup_logger
from src.popup_handler import show_copy_confirmation
from src.setup_dialog import show_setup_dialog
from src.tray_app import TrayApp



class PDFMigrationApp:
    """
    PDF移行ツールのメインアプリケーションクラス。

    各モジュールを統合し、アプリケーションのライフサイクルを管理する。
    """

    def __init__(self) -> None:
        self._logger = setup_logger()
        self._config: dict = {}
        self._watcher: FileWatcher | None = None
        self._tray: TrayApp | None = None
        self._is_watching: bool = False
        # ポップアップの排他制御用ロック
        self._popup_lock = threading.Lock()
        # 履歴管理インスタンスの生成
        self._history = HistoryManager()
        # 直近で処理したファイルのタイムスタンプ記録（デバウンス用）
        self._recently_processed: dict[str, float] = {}



    def run(self) -> None:
        """アプリケーションを起動する。"""
        self._logger.info("========== PDF移行ツールを起動します ==========")

        try:
            # 設定の読み込み or 初回設定
            if not self._initialize_config():
                self._logger.info("設定が完了しませんでした。アプリケーションを終了します。")
                return

            # フォルダ監視の開始
            self._start_watching()

            # システムトレイの起動（メインスレッドでブロッキング）
            self._start_tray()

        except KeyboardInterrupt:
            self._logger.info("キーボード割り込みを検知しました。")
        except Exception as e:
            self._logger.error(f"予期しないエラーが発生しました: {e}", exc_info=True)
        finally:
            self._cleanup()

    def _initialize_config(self) -> bool:
        """
        設定を初期化する。

        初回起動時はGUIダイアログで設定を行い、
        設定ファイルが存在する場合はそこから読み込む。

        Returns:
            設定が正常に完了した場合はTrue
        """
        if is_first_launch():
            self._logger.info("初回起動を検知しました。設定ダイアログを表示します。")
            config = show_setup_dialog()

            if config is None:
                return False

            save_config(config)
            self._config = config
        else:
            self._config = load_config()

        # バリデーション
        errors = validate_config(self._config)
        if errors:
            self._logger.error(f"設定エラー: {', '.join(errors)}")

            # エラーがある場合は再設定ダイアログを表示
            config = show_setup_dialog(self._config)
            if config is None:
                return False

            save_config(config)
            self._config = config

            # 再バリデーション
            errors = validate_config(self._config)
            if errors:
                self._logger.error(f"設定エラーが解消されていません: {', '.join(errors)}")
                return False

        self._logger.info(f"監視フォルダ: {self._config['watch_folder']}")
        self._logger.info(f"移動先フォルダ: {self._config['destination_folder']}")
        return True

    def _on_new_file_detected(self, file_path: str) -> None:
        """
        新しいファイルが検知されたときのコールバック。

        ポップアップを表示し、ユーザーの選択に基づいてファイルをコピーする。
        スレッドセーフに実行するため、ロックを使用。

        Args:
            file_path: 検知されたファイルのパス
        """
        # Obtain the timestamp immediately when the event is triggered (before lock)
        # to prevent debounce logic from being bypassed due to user lock-holding time.
        now = time.time()
        filename = os.path.basename(file_path)

        # ポップアップが同時に複数表示されないようロックを取得
        with self._popup_lock:
            # 既に処理済み（サイズも更新日時も同一）の場合はスキップ
            if not self._history.should_process_file(file_path):
                return

            # 短時間（5秒以内）の同一ファイルイベントを重複排除（デバウンス）
            if filename in self._recently_processed:
                if now - self._recently_processed[filename] < 5.0:
                    self._logger.debug(f"重複検知によりスキップ (デバウンス): {filename}")
                    return
            self._recently_processed[filename] = now


            self._logger.info(f"新しいPDFを検知しました: {file_path}")

            destination_folder = self._config["destination_folder"]

            # ポップアップ表示（メインスレッド以外からの呼び出し対応）
            confirmed = show_copy_confirmation(file_path, destination_folder)

            if confirmed:
                result = copy_file(file_path, destination_folder)
                if result:
                    self._logger.info(f"ファイルコピー完了: {result}")
                    # コピーに成功した場合は、履歴に記録する
                    self._history.record_processed_file(file_path)
                else:
                    self._logger.error("ファイルのコピーに失敗しました。")
            else:
                self._logger.info("ユーザーがファイルコピーをスキップしました。")
                # スキップした場合も、そのファイルが更新されない限りは
                # 再ポップアップしないように履歴に記録する
                self._history.record_processed_file(file_path)



    def _start_watching(self) -> None:
        """フォルダ監視を開始する。"""
        self._watcher = FileWatcher(
            watch_folder=self._config["watch_folder"],
            file_extensions=self._config.get("file_extensions", [".pdf"]),
            on_new_file=self._on_new_file_detected,
        )
        self._watcher.start()
        self._is_watching = True

    def _stop_watching(self) -> None:
        """フォルダ監視を停止する。"""
        if self._watcher:
            self._watcher.stop()
            self._is_watching = False

    def _toggle_watching(self) -> None:
        """監視の開始/停止を切り替える。"""
        if self._is_watching:
            self._stop_watching()
            self._logger.info("監視を停止しました。")
            if self._tray:
                self._tray.update_tooltip("PDF移行ツール - 停止中")
        else:
            self._start_watching()
            self._logger.info("監視を再開しました。")
            if self._tray:
                self._tray.update_tooltip("PDF移行ツール - 監視中")

    def _open_settings(self) -> None:
        """設定画面を開く。"""
        self._logger.info("設定変更ダイアログを表示します。")

        # 一時的に監視を停止
        was_watching = self._is_watching
        if was_watching:
            self._stop_watching()

        config = show_setup_dialog(self._config)

        if config is not None:
            self._config = config
            save_config(config)
            self._logger.info("設定を更新しました。")

        # 監視を再開
        if was_watching or config is not None:
            self._start_watching()

    def _quit_app(self) -> None:
        """アプリケーションを終了する。"""
        self._cleanup()

    def _get_watch_status(self) -> bool:
        """監視状態を返す。"""
        return self._is_watching

    def _start_tray(self) -> None:
        """システムトレイを起動する。"""
        self._tray = TrayApp(
            on_open_settings=self._open_settings,
            on_toggle_watch=self._toggle_watching,
            on_quit=self._quit_app,
            get_watch_status=self._get_watch_status,
        )
        self._tray.start()

    def _cleanup(self) -> None:
        """リソースのクリーンアップを行う。"""
        self._logger.info("アプリケーションを終了します。")
        self._stop_watching()
        if self._tray:
            self._tray.stop()
        self._logger.info("========== PDF移行ツールを終了しました ==========")


def main() -> None:
    """メインエントリーポイント。"""
    app = PDFMigrationApp()
    app.run()


if __name__ == "__main__":
    main()
