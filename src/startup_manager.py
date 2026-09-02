"""
スタートアップ自動登録管理モジュール

Windowsのスタートアップフォルダ（shell:startup）への
ショートカット自動作成・削除・状態確認を行う。
"""

import os
import subprocess
import sys

from src.logger import get_logger

SHORTCUT_NAME: str = "デザイン依頼書データフォルダ移行ツール.lnk"


def get_startup_folder() -> str:
    """Windowsのスタートアップフォルダのパスを取得する。"""
    appdata = os.environ.get("APPDATA", "")
    if not appdata:
        appdata = os.path.expanduser("~\\AppData\\Roaming")
    return os.path.join(appdata, r"Microsoft\Windows\Start Menu\Programs\Startup")


def get_shortcut_path() -> str:
    """スタートアップショートカットの完全パスを取得する。"""
    return os.path.join(get_startup_folder(), SHORTCUT_NAME)


def is_startup_registered() -> bool:
    """スタートアップにショートカットが登録されているか確認する。"""
    return os.path.exists(get_shortcut_path())


def create_startup_shortcut() -> bool:
    """
    スタートアップフォルダに本ツールのショートカットを自動作成する。

    Returns:
        作成成功時 True、失敗時 False
    """
    logger = get_logger()
    try:
        # 実行ファイルのパスと作業ディレクトリを決定
        if getattr(sys, "frozen", False):
            target_path = sys.executable
            working_dir = os.path.dirname(sys.executable)
        else:
            target_path = os.path.abspath(sys.argv[0])
            working_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        startup_folder = get_startup_folder()
        os.makedirs(startup_folder, exist_ok=True)
        shortcut_path = get_shortcut_path()

        # PowerShell の WScript.Shell を利用してショートカットを作成
        ps_script = f"""
        $WshShell = New-Object -ComObject WScript.Shell
        $Shortcut = $WshShell.CreateShortcut('{shortcut_path}')
        $Shortcut.TargetPath = '{target_path}'
        $Shortcut.WorkingDirectory = '{working_dir}'
        $Shortcut.Description = 'デザイン依頼書データフォルダ移行ツール'
        $Shortcut.Save()
        """

        subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_script],
            check=True,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000),
        )

        logger.info(f"スタートアップにショートカットを作成しました: {shortcut_path} -> {target_path}")
        return True

    except Exception as e:
        logger.error(f"スタートアップショートカット作成に失敗しました: {e}", exc_info=True)
        return False


def remove_startup_shortcut() -> bool:
    """
    スタートアップフォルダからショートカットを削除する。

    Returns:
        削除成功時（または元から存在しない場合）True、失敗時 False
    """
    logger = get_logger()
    shortcut_path = get_shortcut_path()
    try:
        if os.path.exists(shortcut_path):
            os.remove(shortcut_path)
            logger.info(f"スタートアップからショートカットを削除しました: {shortcut_path}")
        return True
    except OSError as e:
        logger.error(f"スタートアップショートカット削除に失敗しました: {e}", exc_info=True)
        return False
