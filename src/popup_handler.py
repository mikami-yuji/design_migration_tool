"""
ポップアップダイアログモジュール

新しいPDFが検知された際に、移動確認のポップアップを表示する。
tkinterを使用したモダンなデザインのダイアログで、PDFの1ページ目をプレビュー表示する機能を備える。
"""

import os
import tkinter as tk
from tkinter import font as tkfont
from typing import Any

from src.logger import get_logger

# Pillow, pypdfium2, PyMuPDF (fitz) のインポート確認と型定義の準備
HAS_PILLOW: bool = False
HAS_PDFIUM: bool = False
HAS_FITZ: bool = False

try:
    from PIL import Image, ImageTk, ImageFilter
    HAS_PILLOW = True
except ImportError:
    pass

try:
    import pypdfium2 as pdfium
    HAS_PDFIUM = True
except ImportError:
    pass

try:
    import fitz  # PyMuPDF (fallback)
    HAS_FITZ = True
except ImportError:
    pass


# カラーパレット定義
COLORS: dict[str, str] = {
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


def render_pdf_page_to_image(
    file_path: str,
    max_width: int = 420,
    max_height: int = 550,
) -> Any:
    """
    指定されたファイルのプレビュー用画像を生成して返す。
    PDFの場合は1ページ目をレンダリングし、一般的な画像形式の場合は直接読み込む。

    Args:
        file_path: 対象ファイルの絶対パス
        max_width: プレビュー領域の最大幅
        max_height: プレビュー領域の最大高さ

    Returns:
        tkinter用の ImageTk.PhotoImage オブジェクト。生成に失敗した場合は None。
    """
    logger = get_logger()

    if not HAS_PILLOW:
        logger.warning("Pillowがインポートできないため、プレビューを生成できません。")
        return None

    if not os.path.exists(file_path):
        logger.warning(f"プレビュー対象ファイルが見つかりません: {file_path}")
        return None

    _, ext = os.path.splitext(file_path.lower())

    # PDFの場合
    if ext == ".pdf":
        # 1. pypdfium2 による安全・高精細レンダリング（優先）
        if HAS_PDFIUM:
            try:
                pdf = pdfium.PdfDocument(file_path)
                if len(pdf) == 0:
                    logger.warning(f"PDFにページが含まれていません: {file_path}")
                    return None
                page = pdf[0]
                # 3倍解像度でレンダリング
                img = page.render(scale=3.0).to_pil()
                img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
                img = img.filter(ImageFilter.SHARPEN)
                return ImageTk.PhotoImage(img)
            except Exception as e:
                logger.error(f"pypdfium2でのPDFプレビュー生成エラー: {e}", exc_info=True)

        # 2. fitz (PyMuPDF) によるフォールバックレンダリング
        if HAS_FITZ:
            doc: fitz.Document | None = None
            try:
                doc = fitz.open(file_path)
                if len(doc) == 0:
                    logger.warning(f"PDFにページが含まれていません: {file_path}")
                    return None

                page = doc.load_page(0)
                zoom_factor: float = 3.0
                matrix = fitz.Matrix(zoom_factor, zoom_factor)
                pixmap = page.get_pixmap(matrix=matrix)

                img = Image.frombytes("RGB", [pixmap.width, pixmap.height], pixmap.samples)
                img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
                img = img.filter(ImageFilter.SHARPEN)
                return ImageTk.PhotoImage(img)
            except Exception as e:
                logger.error(f"fitzでのPDFプレビュー生成エラー: {e}", exc_info=True)
            finally:
                if doc is not None:
                    try:
                        doc.close()
                    except Exception:
                        pass

        logger.warning("利用可能なPDFレンダラー（pypdfium2 または fitz）がありません。")
        return None

    # 一般的な画像形式の場合
    elif ext in [".png", ".jpg", ".jpeg", ".gif", ".bmp"]:
        try:
            img = Image.open(file_path)
            img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
            # 一般画像もシャープ化を施してくっきり表示
            img = img.filter(ImageFilter.SHARPEN)
            photo_img = ImageTk.PhotoImage(img)
            return photo_img
        except Exception as e:
            logger.error(f"画像プレビューの生成中にエラーが発生しました: {e}", exc_info=True)
            return None

    # その他の未対応ファイル
    return None


def open_large_preview(
    file_path: str,
    parent: tk.Tk,
) -> None:
    """
    プレビュー画像を別ウィンドウで超高解像度で拡大表示する。

    Args:
        file_path: 対象ファイルの絶対パス
        parent: 親ウィンドウ (tk.Tk)
    """
    logger = get_logger()

    # 拡大用ウィンドウ (Toplevel) の作成
    top = tk.Toplevel(parent)
    top.title("拡大プレビュー")
    top.configure(bg=COLORS["bg"])

    # 常に最前面に表示
    top.attributes("-topmost", True)

    # 画面の高さに応じて拡大ウィンドウのサイズを動的に決定 (アスペクト比 1:1.414 の維持)
    screen_height = top.winfo_screenheight()
    large_height = int(screen_height * 0.85)
    large_width = int(large_height / 1.414)

    screen_width = top.winfo_screenwidth()
    x_position = (screen_width - large_width) // 2
    y_position = (screen_height - large_height) // 2
    top.geometry(f"{large_width}x{large_height}+{x_position}+{y_position}")

    # タイトルラベル
    title_label = tk.Label(
        top,
        text="📄 拡大プレビュー (クリックで閉じます)",
        font=tkfont.Font(family="Yu Gothic UI", size=12, weight="bold"),
        fg=COLORS["accent"],
        bg=COLORS["bg"],
        pady=10,
    )
    title_label.pack(fill=tk.X)

    # 画像を表示するカード型フレーム
    preview_card = tk.Frame(
        top,
        bg=COLORS["surface"],
        bd=1,
        relief=tk.SOLID,
        highlightbackground=COLORS["border"],
        highlightcolor=COLORS["border"],
        highlightthickness=1,
    )
    preview_card.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

    # 超高解像度画像用サイズ
    max_w = large_width - 40
    max_h = large_height - 60

    # 拡大プレビュー用に 4.5倍 などの超高解像度画像を取得 (zoom=4.5でさらに極限まで高精細化)
    large_image = render_pdf_page_to_image(
        file_path=file_path,
        max_width=max_w,
        max_height=max_h,
    )

    if large_image is not None:
        image_label = tk.Label(
            preview_card,
            image=large_image,
            bg=COLORS["surface"],
            cursor="hand2",
        )
        image_label.image = large_image  # 参照保持
        image_label.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # クリックで拡大ウィンドウを閉じる
        image_label.bind("<Button-1>", lambda e: top.destroy())
        top.bind("<Button-1>", lambda e: top.destroy())
    else:
        fallback_text = tk.Label(
            preview_card,
            text="拡大プレビューの生成に失敗しました。",
            font=tkfont.Font(family="Yu Gothic UI", size=12),
            fg=COLORS["text_secondary"],
            bg=COLORS["surface"],
        )
        fallback_text.pack(expand=True)
        top.bind("<Button-1>", lambda e: top.destroy())


def show_copy_confirmation(
    file_path: str,
    destination_folder: str,
) -> bool:
    """
    ファイルコピー確認ポップアップを表示する（プレビュー付き）。

    Args:
        file_path: 検知されたファイルのパス
        destination_folder: コピー先フォルダのパス

    Returns:
        ユーザーが「はい」を選択した場合はTrue、「いいえ」の場合はFalse
    """
    logger = get_logger()
    result: bool = False

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

    # DPI Awarenessの設定 (Windows用で高解像度ディスプレイ時のボケを防止)
    import ctypes
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2) # Per Monitor DPI Aware
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

    # ルートウィンドウの作成
    root = tk.Tk()
    root.title("PDF移行ツール")
    root.configure(bg=COLORS["bg"])
    root.resizable(False, False)

    # プレビュー付きの広めのウィンドウサイズと中央配置（960x660）
    window_width: int = 960
    window_height: int = 660
    screen_width: int = root.winfo_screenwidth()
    screen_height: int = root.winfo_screenheight()
    x_position: int = (screen_width - window_width) // 2
    y_position: int = (screen_height - window_height) // 2
    root.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")

    # 常に最前面に表示
    root.attributes("-topmost", True)

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

    # メインフレーム (全体を囲うパディング付きの外枠)
    main_frame = tk.Frame(root, bg=COLORS["bg"], padx=30, pady=25)
    main_frame.pack(fill=tk.BOTH, expand=True)

    # 左右分割レイアウト用のコンテナ
    split_container = tk.Frame(main_frame, bg=COLORS["bg"])
    split_container.pack(fill=tk.BOTH, expand=True)

    # ------------------- 左カラム (プレビュー表示領域) -------------------
    left_frame = tk.Frame(split_container, bg=COLORS["bg"], width=460)
    left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 30))
    left_frame.pack_propagate(False)  # 左カラムの幅を460に固定

    # プレビュー領域のヘッダータイトル
    preview_title_label = tk.Label(
        left_frame,
        text="📄 用紙プレビュー (1ページ目)",
        font=title_font,
        fg=COLORS["accent"],
        bg=COLORS["bg"],
        anchor=tk.W,
    )
    preview_title_label.pack(fill=tk.X, pady=(0, 10))

    # プレビュー画像を表示するカード型フレーム
    preview_card = tk.Frame(
        left_frame,
        bg=COLORS["surface"],
        bd=1,
        relief=tk.SOLID,
        highlightbackground=COLORS["border"],
        highlightcolor=COLORS["border"],
        highlightthickness=1,
    )
    preview_card.pack(fill=tk.BOTH, expand=True)

    # プレビュー画像のレンダリング試行
    preview_image: ImageTk.PhotoImage | None = render_pdf_page_to_image(
        file_path=file_path,
        max_width=420,
        max_height=550,
    )

    if preview_image is not None:
        # 画像がある場合はラベルに貼り付けて表示 (クリックで拡大)
        image_label = tk.Label(
            preview_card,
            image=preview_image,
            bg=COLORS["surface"],
            cursor="hand2",
        )
        image_label.image = preview_image  # ガベージコレクション防止用の参照保持
        image_label.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 左クリックされたら超高精細の拡大プレビューウィンドウを開く
        image_label.bind("<Button-1>", lambda event: open_large_preview(file_path, root))

        # ユーザーにクリック可能であることを示す小さなヒントテキストを追加
        hint_label = tk.Label(
            left_frame,
            text="🔍 画像をクリックすると超高解像度で拡大表示します",
            font=tkfont.Font(family="Yu Gothic UI", size=9),
            fg=COLORS["accent"],
            bg=COLORS["bg"],
        )
        hint_label.pack(pady=(8, 0))
    else:
        # プレビューが取得できなかった場合の安全なフォールバック
        fallback_frame = tk.Frame(preview_card, bg=COLORS["surface"])
        fallback_frame.pack(fill=tk.BOTH, expand=True)

        fallback_icon = tk.Label(
            fallback_frame,
            text="⚠️",
            font=tkfont.Font(size=40),
            fg=COLORS["text_secondary"],
            bg=COLORS["surface"],
        )
        fallback_icon.pack(expand=True, pady=(130, 0))

        fallback_text = tk.Label(
            fallback_frame,
            text="プレビューを表示できません\n\n(ファイルが使用中であるか、\n未対応のフォーマットです)",
            font=label_font,
            fg=COLORS["text_secondary"],
            bg=COLORS["surface"],
            justify=tk.CENTER,
        )
        fallback_text.pack(expand=True, pady=(0, 130))

    # ------------------- 右カラム (情報・アクション領域) -------------------
    right_frame = tk.Frame(split_container, bg=COLORS["bg"])
    right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

    # アイコン + メインタイトル
    title_frame = tk.Frame(right_frame, bg=COLORS["bg"])
    title_frame.pack(fill=tk.X, pady=(0, 20))

    icon_label = tk.Label(
        title_frame,
        text="🔔",
        font=tkfont.Font(size=24),
        bg=COLORS["bg"],
    )
    icon_label.pack(side=tk.LEFT, padx=(0, 10))

    title_label = tk.Label(
        title_frame,
        text="新しいファイルを検知しました",
        font=title_font,
        fg=COLORS["accent"],
        bg=COLORS["bg"],
    )
    title_label.pack(side=tk.LEFT)

    # ファイル情報表示用のカード型フレーム
    info_frame = tk.Frame(right_frame, bg=COLORS["surface"], padx=20, pady=20)
    info_frame.pack(fill=tk.X, pady=(0, 25))

    # ファイル名
    filename: str = os.path.basename(file_path)
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
        wraplength=420,
    )
    file_value.pack(fill=tk.X, pady=(0, 12))

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
        wraplength=420,
    )
    dest_value.pack(fill=tk.X)

    # 移行確認メッセージ
    confirm_label = tk.Label(
        right_frame,
        text="元のファイルを残したまま、このデータを指定のフォルダに移しますか？",
        font=label_font,
        fg=COLORS["text"],
        bg=COLORS["bg"],
        justify=tk.LEFT,
        wraplength=460,
    )
    confirm_label.pack(pady=(0, 30), fill=tk.X)

    # ボタン操作フレーム
    button_frame = tk.Frame(right_frame, bg=COLORS["bg"])
    button_frame.pack(anchor=tk.W)

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
        width=14,
        height=1,
        command=on_confirm,
    )
    yes_button.pack(side=tk.LEFT, padx=(0, 20))

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
        width=14,
        height=1,
        command=on_cancel,
    )
    no_button.pack(side=tk.LEFT)

    # ホバー時の配色アニメーションイベント
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

    # ウィンドウクローズ（右上の「×」ボタン）時の処理
    root.protocol("WM_DELETE_WINDOW", on_cancel)

    # ポップアップ時のアラートベル音を鳴らす
    root.bell()

    # イベントループ開始
    root.mainloop()

    return result
