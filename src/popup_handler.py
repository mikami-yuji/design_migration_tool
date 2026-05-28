"""
ポップアップダイアログモジュール

新しいPDFが検知された際に、移動確認のポップアップを表示する。
tkinterを使用したモダンなデザインのダイアログ。
"""

import os
import tkinter as tk
from tkinter import font as tkfont

from src.logger import get_logger


# カラーパレット定義
COLORS = {
    "bg": "#1e1e2e",
    "surface": "#2a2a3e",
    "primary": "#7c6ff5",
    "primary_hover": "#6a5ce0",
    "danger": "#e85d75",
    "danger_hover": "#d14960",
    "text": "#e0e0e8",
    "text_secondary": "#a0a0b4",
    "border": "#3a3a52",
    "accent": "#4ec9b0",
}


def show_copy_confirmation(
    file_path: str,
    destination_folder: str,
) -> bool:
    """
    ファイルコピー確認ポップアップを表示する。

    Args:
        file_path: 検知されたファイルのパス
        destination_folder: コピー先フォルダ of パス

    Returns:
        ユーザーが「はい」を選択した場合はTrue、「いいえ」の場合はFalse
    """
    logger = get_logger()
    result = False

    def on_confirm() -> None:
        nonlocal result
        result = True
        logger.info(f"ユーザーがファイルコピーを承認しました: {file_path}")
        root.destroy()

    def on_cancel() -> None:
        nonlocal result
        result = False
        logger.info(f"ユーザーがファイルコピーをキャンセルしました: {file_path}")
        root.destroy()

    # ルートウィンドウの作成
    root = tk.Tk()
    root.title("PDF移行ツール")
    root.configure(bg=COLORS["bg"])
    root.resizable(False, False)

    # ウィンドウサイズと中央配置
    window_width = 520
    window_height = 300
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x_position = (screen_width - window_width) // 2
    y_position = (screen_height - window_height) // 2
    root.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")

    # 常に最前面に表示
    root.attributes("-topmost", True)

    # ウィンドウ枠の装飾を最小化
    root.overrideredirect(False)

    # フォント定義
    try:
        title_font = tkfont.Font(family="Yu Gothic UI", size=14, weight="bold")
        label_font = tkfont.Font(family="Yu Gothic UI", size=10)
        path_font = tkfont.Font(family="Consolas", size=9)
        button_font = tkfont.Font(family="Yu Gothic UI", size=11, weight="bold")
    except Exception:
        title_font = tkfont.Font(size=14, weight="bold")
        label_font = tkfont.Font(size=10)
        path_font = tkfont.Font(size=9)
        button_font = tkfont.Font(size=11, weight="bold")

    # メインフレーム
    main_frame = tk.Frame(root, bg=COLORS["bg"], padx=30, pady=20)
    main_frame.pack(fill=tk.BOTH, expand=True)

    # アイコン + タイトル
    title_frame = tk.Frame(main_frame, bg=COLORS["bg"])
    title_frame.pack(fill=tk.X, pady=(0, 15))

    icon_label = tk.Label(
        title_frame,
        text="📄",
        font=tkfont.Font(size=24),
        bg=COLORS["bg"],
    )
    icon_label.pack(side=tk.LEFT, padx=(0, 10))

    title_label = tk.Label(
        title_frame,
        text="新しいPDFが検知されました",
        font=title_font,
        fg=COLORS["accent"],
        bg=COLORS["bg"],
    )
    title_label.pack(side=tk.LEFT)

    # 情報セクション
    info_frame = tk.Frame(main_frame, bg=COLORS["surface"], padx=15, pady=12)
    info_frame.pack(fill=tk.X, pady=(0, 10))

    # ファイル名
    filename = os.path.basename(file_path)
    file_label = tk.Label(
        info_frame,
        text="ファイル名:",
        font=label_font,
        fg=COLORS["text_secondary"],
        bg=COLORS["surface"],
        anchor=tk.W,
    )
    file_label.pack(fill=tk.X)

    file_value = tk.Label(
        info_frame,
        text=filename,
        font=path_font,
        fg=COLORS["text"],
        bg=COLORS["surface"],
        anchor=tk.W,
    )
    file_value.pack(fill=tk.X, pady=(0, 8))

    # コピー先
    dest_label = tk.Label(
        info_frame,
        text="コピー先フォルダ:",
        font=label_font,
        fg=COLORS["text_secondary"],
        bg=COLORS["surface"],
        anchor=tk.W,
    )
    dest_label.pack(fill=tk.X)

    dest_value = tk.Label(
        info_frame,
        text=destination_folder,
        font=path_font,
        fg=COLORS["text"],
        bg=COLORS["surface"],
        anchor=tk.W,
        wraplength=440,
    )
    dest_value.pack(fill=tk.X)

    # 確認メッセージ
    confirm_label = tk.Label(
        main_frame,
        text="元のファイルを残したまま、このデータを指定のフォルダに移しますか？",
        font=label_font,
        fg=COLORS["text"],
        bg=COLORS["bg"],
    )
    confirm_label.pack(pady=(10, 15))


    # ボタンフレーム
    button_frame = tk.Frame(main_frame, bg=COLORS["bg"])
    button_frame.pack()

    # 「はい」ボタン
    yes_button = tk.Button(
        button_frame,
        text="✓  はい",
        font=button_font,
        fg="white",
        bg=COLORS["primary"],
        activebackground=COLORS["primary_hover"],
        activeforeground="white",
        relief=tk.FLAT,
        cursor="hand2",
        width=12,
        height=1,
        command=on_confirm,
    )
    yes_button.pack(side=tk.LEFT, padx=(0, 15))

    # 「いいえ」ボタン
    no_button = tk.Button(
        button_frame,
        text="✕  いいえ",
        font=button_font,
        fg="white",
        bg=COLORS["danger"],
        activebackground=COLORS["danger_hover"],
        activeforeground="white",
        relief=tk.FLAT,
        cursor="hand2",
        width=12,
        height=1,
        command=on_cancel,
    )
    no_button.pack(side=tk.LEFT)

    # ホバーエフェクト
    def on_enter_yes(event: tk.Event) -> None:
        yes_button.config(bg=COLORS["primary_hover"])

    def on_leave_yes(event: tk.Event) -> None:
        yes_button.config(bg=COLORS["primary"])

    def on_enter_no(event: tk.Event) -> None:
        no_button.config(bg=COLORS["danger_hover"])

    def on_leave_no(event: tk.Event) -> None:
        no_button.config(bg=COLORS["danger"])

    yes_button.bind("<Enter>", on_enter_yes)
    yes_button.bind("<Leave>", on_leave_yes)
    no_button.bind("<Enter>", on_enter_no)
    no_button.bind("<Leave>", on_leave_no)

    # ウィンドウクローズ時の処理
    root.protocol("WM_DELETE_WINDOW", on_cancel)

    # ベルを鳴らして注意を引く
    root.bell()

    # イベントループ開始
    root.mainloop()

    return result
