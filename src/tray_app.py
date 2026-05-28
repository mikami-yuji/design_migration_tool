"""
システムトレイ常駐モジュール

pystrayを使用してシステムトレイにアイコンを表示し、
アプリケーションの操作メニューを提供する。
"""

import threading
from typing import Any, Callable

import pystray
from PIL import Image, ImageDraw, ImageFont

from src.logger import get_logger


def create_tray_icon_image() -> Image.Image:
    """
    トレイアイコン用の画像を生成する。

    PDFを連想させるドキュメントアイコンを描画する。

    Returns:
        生成されたアイコン画像
    """
    size = 64
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    # ドキュメント本体（角丸風の四角形）
    draw.rectangle([8, 4, 52, 60], fill="#7c6ff5", outline="#6a5ce0", width=2)

    # 折り返し部分（右上の三角）
    draw.polygon([(38, 4), (52, 18), (38, 18)], fill="#4ec9b0")

    # テキスト「PDF」
    try:
        font = ImageFont.truetype("arial.ttf", 14)
    except OSError:
        font = ImageFont.load_default()

    draw.text((14, 28), "PDF", fill="white", font=font)

    # 矢印（移動を示す → マーク）
    draw.polygon([(54, 38), (62, 44), (54, 50)], fill="#4ec9b0")
    draw.rectangle([46, 41, 54, 47], fill="#4ec9b0")

    return image


class TrayApp:
    """
    システムトレイアプリケーション。

    トレイアイコンのメニューから監視の開始/停止、設定変更、終了を操作可能。
    """

    def __init__(
        self,
        on_open_settings: Callable[[], None],
        on_toggle_watch: Callable[[], None],
        on_quit: Callable[[], None],
        get_watch_status: Callable[[], bool],
    ) -> None:
        """
        Args:
            on_open_settings: 設定画面を開くコールバック
            on_toggle_watch: 監視の開始/停止を切り替えるコールバック
            on_quit: アプリケーション終了のコールバック
            get_watch_status: 監視状態を取得するコールバック
        """
        self._on_open_settings = on_open_settings
        self._on_toggle_watch = on_toggle_watch
        self._on_quit = on_quit
        self._get_watch_status = get_watch_status
        self._icon: pystray.Icon | None = None
        self._logger = get_logger()

    def _create_menu(self) -> pystray.Menu:
        """トレイメニューを作成する。"""
        return pystray.Menu(
            pystray.MenuItem(
                "監視状態",
                None,
                enabled=False,
                default=True,
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                lambda item: "⏸ 監視を停止" if self._get_watch_status() else "▶ 監視を開始",
                self._handle_toggle_watch,
            ),
            pystray.MenuItem(
                "⚙ 設定変更",
                self._handle_open_settings,
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "✕ 終了",
                self._handle_quit,
            ),
        )

    def _handle_toggle_watch(self, icon: Any, item: Any) -> None:
        """監視の切り替えハンドラ。"""
        self._on_toggle_watch()
        # メニュー表示を更新
        if self._icon:
            self._icon.update_menu()

    def _handle_open_settings(self, icon: Any, item: Any) -> None:
        """設定画面を開くハンドラ。"""
        self._on_open_settings()

    def _handle_quit(self, icon: Any, item: Any) -> None:
        """アプリケーション終了ハンドラ。"""
        self._logger.info("トレイからアプリケーションの終了が要求されました。")
        if self._icon:
            self._icon.stop()
        self._on_quit()

    def start(self) -> None:
        """システムトレイにアイコンを表示する。"""
        icon_image = create_tray_icon_image()

        self._icon = pystray.Icon(
            name="pdf_migration_tool",
            icon=icon_image,
            title="PDF移行ツール - 監視中",
            menu=self._create_menu(),
        )

        self._logger.info("システムトレイにアイコンを表示しました。")

        # トレイアイコンのメインループを開始（ブロッキング）
        self._icon.run()

    def start_threaded(self) -> threading.Thread:
        """システムトレイをバックグラウンドスレッドで起動する。"""
        tray_thread = threading.Thread(target=self.start, daemon=True)
        tray_thread.start()
        return tray_thread

    def stop(self) -> None:
        """トレイアイコンを停止する。"""
        if self._icon:
            self._icon.stop()
            self._icon = None
            self._logger.info("システムトレイアイコンを停止しました。")

    def update_tooltip(self, text: str) -> None:
        """トレイアイコンのツールチップを更新する。"""
        if self._icon:
            self._icon.title = text
