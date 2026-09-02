"""
初回設定ダイアログモジュール

初回起動時やユーザーが設定変更を選択した際に、
監視フォルダと移動先フォルダをGUIで選択できるダイアログを表示する。
"""

import os
import tkinter as tk
from tkinter import filedialog, font as tkfont, messagebox
from typing import Any

from src.logger import get_logger


# カラーパレット定義
COLORS = {
    "bg": "#1e1e2e",
    "surface": "#2a2a3e",
    "primary": "#7c6ff5",
    "primary_hover": "#6a5ce0",
    "text": "#e0e0e8",
    "text_secondary": "#a0a0b4",
    "border": "#3a3a52",
    "accent": "#4ec9b0",
    "input_bg": "#333348",
    "success": "#4ec9b0",
    "success_hover": "#3db89f",
}


def show_setup_dialog(current_config: dict[str, Any] | None = None) -> dict[str, Any] | None:
    """
    フォルダ設定ダイアログを表示する。

    監視フォルダと移動先フォルダをGUIで選択できる。
    既存の設定がある場合はそれを初期値として表示。

    Args:
        current_config: 現在の設定内容（編集時に使用）

    Returns:
        設定内容の辞書。キャンセル時はNone。
    """
    logger = get_logger()
    result: dict[str, Any] | None = None

    root = tk.Tk()
    root.title("📂 PDF移行ツール - 初期設定")
    root.configure(bg=COLORS["bg"])
    root.resizable(False, False)

    # ウィンドウサイズと中央配置
    window_width = 600
    window_height = 450
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x_position = (screen_width - window_width) // 2
    y_position = (screen_height - window_height) // 2
    root.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")

    root.attributes("-topmost", True)

    # フォント定義
    try:
        title_font = tkfont.Font(family="Yu Gothic UI", size=16, weight="bold")
        subtitle_font = tkfont.Font(family="Yu Gothic UI", size=10)
        label_font = tkfont.Font(family="Yu Gothic UI", size=11, weight="bold")
        entry_font = tkfont.Font(family="Consolas", size=10)
        button_font = tkfont.Font(family="Yu Gothic UI", size=10, weight="bold")
        save_button_font = tkfont.Font(family="Yu Gothic UI", size=12, weight="bold")
    except Exception:
        title_font = tkfont.Font(size=16, weight="bold")
        subtitle_font = tkfont.Font(size=10)
        label_font = tkfont.Font(size=11, weight="bold")
        entry_font = tkfont.Font(size=10)
        button_font = tkfont.Font(size=10, weight="bold")
        save_button_font = tkfont.Font(size=12, weight="bold")

    # メインフレーム
    main_frame = tk.Frame(root, bg=COLORS["bg"], padx=35, pady=25)
    main_frame.pack(fill=tk.BOTH, expand=True)

    # タイトル
    title_label = tk.Label(
        main_frame,
        text="⚙️  PDF移行ツール 初期設定",
        font=title_font,
        fg=COLORS["accent"],
        bg=COLORS["bg"],
    )
    title_label.pack(anchor=tk.W, pady=(0, 5))

    subtitle_label = tk.Label(
        main_frame,
        text="監視フォルダと移動先フォルダを設定してください",
        font=subtitle_font,
        fg=COLORS["text_secondary"],
        bg=COLORS["bg"],
    )
    subtitle_label.pack(anchor=tk.W, pady=(0, 20))

    # 区切り線
    separator = tk.Frame(main_frame, bg=COLORS["border"], height=1)
    separator.pack(fill=tk.X, pady=(0, 20))

    # --- 監視フォルダ設定 ---
    watch_label = tk.Label(
        main_frame,
        text="📁 監視フォルダ（PDFが生成されるフォルダ）",
        font=label_font,
        fg=COLORS["text"],
        bg=COLORS["bg"],
    )
    watch_label.pack(anchor=tk.W, pady=(0, 5))

    watch_frame = tk.Frame(main_frame, bg=COLORS["bg"])
    watch_frame.pack(fill=tk.X, pady=(0, 20))

    watch_var = tk.StringVar(
        value=current_config.get("watch_folder", "") if current_config else ""
    )
    watch_entry = tk.Entry(
        watch_frame,
        textvariable=watch_var,
        font=entry_font,
        bg=COLORS["input_bg"],
        fg=COLORS["text"],
        insertbackground=COLORS["text"],
        relief=tk.FLAT,
        highlightthickness=1,
        highlightbackground=COLORS["border"],
        highlightcolor=COLORS["primary"],
    )
    watch_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=6)

    def browse_watch_folder() -> None:
        """監視フォルダ選択ダイアログを開く。"""
        folder = filedialog.askdirectory(
            title="監視フォルダを選択してください",
            initialdir=watch_var.get() or os.path.expanduser("~"),
        )
        if folder:
            watch_var.set(folder)

    watch_browse_btn = tk.Button(
        watch_frame,
        text="参照...",
        font=button_font,
        fg="white",
        bg=COLORS["primary"],
        activebackground=COLORS["primary_hover"],
        activeforeground="white",
        relief=tk.FLAT,
        cursor="hand2",
        command=browse_watch_folder,
        padx=15,
    )
    watch_browse_btn.pack(side=tk.RIGHT, padx=(10, 0), ipady=4)

    # --- 移動先フォルダ設定 ---
    dest_label = tk.Label(
        main_frame,
        text="📂 移動先フォルダ（PDFの保存先フォルダ）",
        font=label_font,
        fg=COLORS["text"],
        bg=COLORS["bg"],
    )
    dest_label.pack(anchor=tk.W, pady=(0, 5))

    dest_frame = tk.Frame(main_frame, bg=COLORS["bg"])
    dest_frame.pack(fill=tk.X, pady=(0, 25))

    dest_var = tk.StringVar(
        value=current_config.get("destination_folder", "") if current_config else ""
    )
    dest_entry = tk.Entry(
        dest_frame,
        textvariable=dest_var,
        font=entry_font,
        bg=COLORS["input_bg"],
        fg=COLORS["text"],
        insertbackground=COLORS["text"],
        relief=tk.FLAT,
        highlightthickness=1,
        highlightbackground=COLORS["border"],
        highlightcolor=COLORS["primary"],
    )
    dest_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=6)

    def browse_dest_folder() -> None:
        """移動先フォルダ選択ダイアログを開く。"""
        folder = filedialog.askdirectory(
            title="移動先フォルダを選択してください",
            initialdir=dest_var.get() or os.path.expanduser("~"),
        )
        if folder:
            dest_var.set(folder)

    dest_browse_btn = tk.Button(
        dest_frame,
        text="参照...",
        font=button_font,
        fg="white",
        bg=COLORS["primary"],
        activebackground=COLORS["primary_hover"],
        activeforeground="white",
        relief=tk.FLAT,
        cursor="hand2",
        command=browse_dest_folder,
        padx=15,
    )
    dest_browse_btn.pack(side=tk.RIGHT, padx=(10, 0), ipady=4)

    # --- スタートアップ自動登録設定 ---
    startup_var = tk.BooleanVar(
        value=current_config.get("run_on_startup", True) if current_config else True
    )
    startup_check = tk.Checkbutton(
        main_frame,
        text="🚀  PC起動時に自動で開始する（スタートアップ登録）",
        variable=startup_var,
        font=label_font,
        fg=COLORS["accent"],
        bg=COLORS["bg"],
        activebackground=COLORS["bg"],
        activeforeground=COLORS["accent"],
        selectcolor=COLORS["input_bg"],
        cursor="hand2",
    )
    startup_check.pack(anchor=tk.W, pady=(0, 20))

    # 区切り線
    separator2 = tk.Frame(main_frame, bg=COLORS["border"], height=1)
    separator2.pack(fill=tk.X, pady=(0, 20))

    # --- ボタンフレーム ---
    button_frame = tk.Frame(main_frame, bg=COLORS["bg"])
    button_frame.pack(fill=tk.X)

    def on_save() -> None:
        """設定を保存して閉じる。"""
        nonlocal result

        watch_folder = watch_var.get().strip()
        dest_folder = dest_var.get().strip()
        run_on_startup = startup_var.get()

        # バリデーション
        if not watch_folder:
            messagebox.showwarning("入力エラー", "監視フォルダを指定してください。", parent=root)
            return
        if not dest_folder:
            messagebox.showwarning("入力エラー", "移動先フォルダを指定してください。", parent=root)
            return
        if not os.path.isdir(watch_folder):
            messagebox.showwarning(
                "入力エラー",
                f"監視フォルダが存在しません:\n{watch_folder}",
                parent=root,
            )
            return
        if watch_folder == dest_folder:
            messagebox.showwarning(
                "入力エラー",
                "監視フォルダと移動先フォルダは異なるフォルダを指定してください。",
                parent=root,
            )
            return

        # スタートアップ自動設定の適用
        try:
            from src.startup_manager import create_startup_shortcut, remove_startup_shortcut
            if run_on_startup:
                create_startup_shortcut()
            else:
                remove_startup_shortcut()
        except Exception as e:
            logger.warning(f"スタートアップ設定の適用中に例外が発生しました: {e}")

        result = {
            "watch_folder": watch_folder,
            "destination_folder": dest_folder,
            "file_extensions": (
                current_config.get("file_extensions", [".pdf"])
                if current_config
                else [".pdf"]
            ),
            "check_interval": (
                current_config.get("check_interval", 1.0)
                if current_config
                else 1.0
            ),
            "show_notification_on_move": True,
            "run_on_startup": run_on_startup,
        }

        logger.info(f"設定を保存します - 監視: {watch_folder}, 移動先: {dest_folder}, 自動起動: {run_on_startup}")
        root.destroy()

    def on_cancel() -> None:
        """設定をキャンセルして閉じる。"""
        nonlocal result
        result = None
        logger.info("設定ダイアログがキャンセルされました。")
        root.destroy()

    # 保存ボタン
    save_button = tk.Button(
        button_frame,
        text="✓  保存して開始",
        font=save_button_font,
        fg="white",
        bg=COLORS["success"],
        activebackground=COLORS["success_hover"],
        activeforeground="white",
        relief=tk.FLAT,
        cursor="hand2",
        command=on_save,
        padx=20,
    )
    save_button.pack(side=tk.RIGHT, ipady=5)

    # キャンセルボタン
    cancel_button = tk.Button(
        button_frame,
        text="キャンセル",
        font=button_font,
        fg=COLORS["text_secondary"],
        bg=COLORS["surface"],
        activebackground=COLORS["border"],
        activeforeground=COLORS["text"],
        relief=tk.FLAT,
        cursor="hand2",
        command=on_cancel,
        padx=15,
    )
    cancel_button.pack(side=tk.RIGHT, padx=(0, 10), ipady=5)

    # ホバーエフェクト
    def bind_hover(button: tk.Button, normal_bg: str, hover_bg: str) -> None:
        button.bind("<Enter>", lambda e: button.config(bg=hover_bg))
        button.bind("<Leave>", lambda e: button.config(bg=normal_bg))

    bind_hover(watch_browse_btn, COLORS["primary"], COLORS["primary_hover"])
    bind_hover(dest_browse_btn, COLORS["primary"], COLORS["primary_hover"])
    bind_hover(save_button, COLORS["success"], COLORS["success_hover"])
    bind_hover(cancel_button, COLORS["surface"], COLORS["border"])

    # ウィンドウクローズ時の処理
    root.protocol("WM_DELETE_WINDOW", on_cancel)

    # イベントループ開始
    root.mainloop()

    return result
