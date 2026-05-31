"""
popup_handler モジュールのテスト
"""

import os
from typing import Any
from unittest.mock import MagicMock, patch
import pytest
from PIL import Image, ImageTk
import fitz

from src.popup_handler import (
    render_pdf_page_to_image,
    show_copy_confirmation,
    COLORS,
)


class TestRenderPdfPageToImage:
    """render_pdf_page_to_image 関数のテスト"""

    def test_存在しないファイルの場合Noneを返す(self) -> None:
        """存在しないファイルを指定した場合、Noneが返ること。"""
        result = render_pdf_page_to_image("nonexistent_file.pdf")
        assert result is None

    def test_未対応の拡張子の場合Noneを返す(self, tmp_path: Any) -> None:
        """未対応の拡張子（.txtなど）のファイルを指定した場合、Noneが返ること。"""
        file_path = os.path.join(str(tmp_path), "test.txt")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("dummy text")

        result = render_pdf_page_to_image(file_path)
        assert result is None

    @patch("PIL.ImageTk.PhotoImage")
    def test_画像ファイルから正常にプレビューを生成できる(self, mock_photo_image: MagicMock, tmp_path: Any) -> None:
        """PNGなどの画像ファイルから正常にプレビュー画像が生成できること。"""
        mock_photo_image.return_value = MagicMock()

        file_path = os.path.join(str(tmp_path), "test.png")
        # 100x100の単純な画像を作成
        img = Image.new("RGB", (100, 100), color="red")
        img.save(file_path)

        result = render_pdf_page_to_image(file_path, max_width=50, max_height=50)
        assert result is not None
        mock_photo_image.assert_called_once()

    @patch("PIL.ImageTk.PhotoImage")
    def test_PDFファイルから正常にプレビューを生成できる(self, mock_photo_image: MagicMock, tmp_path: Any) -> None:
        """PDFファイルの1ページ目から正常にプレビュー画像が生成できること。"""
        mock_photo_image.return_value = MagicMock()

        file_path = os.path.join(str(tmp_path), "test.pdf")
        
        # PyMuPDF を使用してダミーの1ページPDFを作成
        doc = fitz.open()
        page = doc.new_page(width=200, height=200)
        # 簡単な図形を描画
        page.draw_rect([10, 10, 100, 100], color=(0, 0, 1), fill=(0, 1, 0))
        doc.save(file_path)
        doc.close()

        result = render_pdf_page_to_image(file_path, max_width=100, max_height=100)
        assert result is not None
        mock_photo_image.assert_called_once()


class TestShowCopyConfirmation:
    """show_copy_confirmation 関数のテスト"""

    @patch("tkinter.Tk")
    def test_ダイアログが表示され確認ボタン押下でTrueを返す(self, mock_tk_class: MagicMock, tmp_path: Any) -> None:
        """ダイアログが表示され、ユーザーが承認（はい）した場合にTrueを返すこと。"""
        mock_root = MagicMock()
        mock_tk_class.return_value = mock_root

        # ダミーのPDFファイルを作成
        file_path = os.path.join(str(tmp_path), "dummy.pdf")
        with open(file_path, "w") as f:
            f.write("dummy")

        # tkinterコントロール作成時等のクラッシュを防ぐため、各種Tkinter要素のパッチを行う
        with patch("tkinter.Button") as mock_button:
            button_instances = []
            
            def create_mock_button(*args: Any, **kwargs: Any) -> MagicMock:
                btn = MagicMock()
                btn.command = kwargs.get("command")
                button_instances.append(btn)
                return btn
            
            mock_button.side_effect = create_mock_button

            with patch("src.popup_handler.render_pdf_page_to_image", return_value=None):
                with patch("tkinter.Frame"), patch("tkinter.Label"), patch("tkinter.font.Font"):
                    def simulate_confirm() -> None:
                        for btn in button_instances:
                            if btn.command and "on_confirm" in btn.command.__name__:
                                btn.command()
                                return
                    
                    mock_root.mainloop = simulate_confirm
                    
                    result = show_copy_confirmation(file_path, "dest_dir")
                    assert result is True

    @patch("tkinter.Tk")
    def test_キャンセルボタン押下でFalseを返す(self, mock_tk_class: MagicMock, tmp_path: Any) -> None:
        """ダイアログが表示され、ユーザーが拒否（いいえ）した場合にFalseを返すこと。"""
        mock_root = MagicMock()
        mock_tk_class.return_value = mock_root

        # ダミーのPDFファイルを作成
        file_path = os.path.join(str(tmp_path), "dummy.pdf")
        with open(file_path, "w") as f:
            f.write("dummy")

        with patch("tkinter.Button") as mock_button:
            button_instances = []
            
            def create_mock_button(*args: Any, **kwargs: Any) -> MagicMock:
                btn = MagicMock()
                btn.command = kwargs.get("command")
                button_instances.append(btn)
                return btn
            
            mock_button.side_effect = create_mock_button

            with patch("src.popup_handler.render_pdf_page_to_image", return_value=None):
                with patch("tkinter.Frame"), patch("tkinter.Label"), patch("tkinter.font.Font"):
                    def simulate_cancel() -> None:
                        for btn in button_instances:
                            if btn.command and "on_cancel" in btn.command.__name__:
                                btn.command()
                                return
                    
                    mock_root.mainloop = simulate_cancel
                    
                    result = show_copy_confirmation(file_path, "dest_dir")
                    assert result is False
