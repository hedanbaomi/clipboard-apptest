#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import signal

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from utils.platform_utils import is_windows, is_macos, get_data_dir
from gui.styles import enable_high_dpi
enable_high_dpi()

from core.clipboard_monitor import ClipboardMonitor
from core.storage import Storage
from core.hotkey import HotkeyManager
from core.autostart import AutoStart
from gui.main_window import MainWindow
from gui.tray import SystemTray


def load_config() -> dict:
    config_path = os.path.join(BASE_DIR, "config.json")
    default_config = {
        "max_history": 100,
        "theme": "light",
        "hotkey": "ctrl+shift+v" if is_windows() else "cmd+shift+v",
        "autostart": True,
        "window_width": 500,
        "window_height": 600,
        "check_interval": 500
    }

    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                default_config.update(config)
        except Exception:
            pass

    return default_config


def get_data_directory() -> str:
    custom_dir = get_data_dir()
    if custom_dir:
        data_dir = os.path.expanduser(custom_dir)
    else:
        data_dir = os.path.join(BASE_DIR, "data")
    os.makedirs(data_dir, exist_ok=True)
    return data_dir


class ClipboardApp:
    def __init__(self):
        self.config = load_config()

        data_dir = get_data_directory()
        self.storage = Storage(data_dir, self.config.get("max_history", 100))

        self.hotkey_manager = HotkeyManager()
        self.autostart = AutoStart()

        self.clipboard_monitor = ClipboardMonitor(
            on_change=self._on_clipboard_change,
            interval=self.config.get("check_interval", 500)
        )

        self.main_window = MainWindow(
            self.config,
            self.storage,
            self.clipboard_monitor,
            self.hotkey_manager,
            self.autostart
        )

        self.tray = SystemTray(
            on_show=self._show_window,
            on_exit=self._exit_app
        )

        self._running = False

    def _on_clipboard_change(self, content):
        if self.main_window:
            self.main_window.on_clipboard_change(content)

    def _show_window(self):
        if self.main_window:
            self.main_window.show()

    def _exit_app(self):
        self._running = False
        self.clipboard_monitor.stop()
        self.hotkey_manager.unregister_all()
        self.tray.stop()

        if self.main_window and self.main_window._root:
            self.main_window._root.quit()

    def run(self):
        self._running = True

        if self.config.get("autostart", False) and not self.autostart.is_enabled():
            self.autostart.enable()

        self.clipboard_monitor.start()

        self.tray.create()
        self.tray.run()

        self.main_window.create()

        try:
            signal.signal(signal.SIGINT, lambda s, f: self._exit_app())
        except Exception:
            pass

        hotkey = self.config.get("hotkey", "ctrl+shift+v")
        print("=" * 50)
        print("  剪切板管理器 已启动")
        print(f"  快捷键: {hotkey.upper()}")
        print("  最小化到系统托盘继续运行")
        print("=" * 50)

        self.main_window.run()

        self._exit_app()


def main():
    try:
        app = ClipboardApp()
        app.run()
    except KeyboardInterrupt:
        print("\n程序已退出")
    except Exception as e:
        print(f"程序错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
