import os
import sys
from typing import Optional

from utils.platform_utils import is_windows, is_macos, get_app_name


class AutoStart:
    def __init__(self):
        self._app_name = get_app_name()
        self._impl = self._create_impl()

    def _create_impl(self):
        if is_windows():
            return _WindowsAutoStart(self._app_name)
        elif is_macos():
            return _MacOSAutoStart(self._app_name)
        else:
            return _LinuxAutoStart(self._app_name)

    def is_enabled(self) -> bool:
        return self._impl.is_enabled()

    def enable(self) -> bool:
        return self._impl.enable()

    def disable(self) -> bool:
        return self._impl.disable()

    def toggle(self) -> bool:
        if self.is_enabled():
            return self.disable()
        else:
            return self.enable()


class _WindowsAutoStart:
    REG_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"

    def __init__(self, app_name: str):
        self._app_name = app_name
        self._exe_path: Optional[str] = None

    @property
    def exe_path(self) -> str:
        if self._exe_path is None:
            if getattr(sys, 'frozen', False):
                self._exe_path = sys.executable
            else:
                python_exe = sys.executable
                script_path = os.path.abspath(sys.argv[0])
                self._exe_path = f'{python_exe}" "{script_path}'
        return self._exe_path

    def _get_registry_value(self) -> str:
        return f'"{self.exe_path}"'

    def is_enabled(self) -> bool:
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.REG_KEY, 0, winreg.KEY_READ)
            try:
                value, _ = winreg.QueryValueEx(key, self._app_name)
                winreg.CloseKey(key)
                return value == self._get_registry_value()
            except FileNotFoundError:
                winreg.CloseKey(key)
                return False
        except Exception:
            return False

    def enable(self) -> bool:
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.REG_KEY, 0, winreg.KEY_WRITE)
            winreg.SetValueEx(key, self._app_name, 0, winreg.REG_SZ, self._get_registry_value())
            winreg.CloseKey(key)
            return True
        except Exception as e:
            print(f"Failed to enable autostart: {e}")
            return False

    def disable(self) -> bool:
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.REG_KEY, 0, winreg.KEY_WRITE)
            try:
                winreg.DeleteValue(key, self._app_name)
            except FileNotFoundError:
                pass
            winreg.CloseKey(key)
            return True
        except Exception as e:
            print(f"Failed to disable autostart: {e}")
            return False


class _MacOSAutoStart:
    def __init__(self, app_name: str):
        self._app_name = app_name
        self._launch_agents_dir = os.path.expanduser("~/Library/LaunchAgents")
        self._plist_path = os.path.join(
            self._launch_agents_dir,
            f"com.{app_name.lower()}.plist"
        )

    def _get_command(self) -> str:
        if getattr(sys, 'frozen', False):
            return sys.executable
        else:
            return f"{sys.executable} {os.path.abspath(sys.argv[0])}"

    def _get_plist_content(self) -> str:
        import shlex
        cmd = self._get_command()
        parts = shlex.split(cmd)
        program = parts[0]
        arguments = " ".join(f"<string>{p}</string>" for p in parts)

        return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.{self._app_name.lower()}</string>
    <key>ProgramArguments</key>
    <array>
        {arguments}
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
    <key>StandardOutPath</key>
    <string>/tmp/{self._app_name.lower()}.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/{self._app_name.lower()}_error.log</string>
</dict>
</plist>"""

    def is_enabled(self) -> bool:
        return os.path.exists(self._plist_path)

    def enable(self) -> bool:
        try:
            os.makedirs(self._launch_agents_dir, exist_ok=True)
            plist_content = self._get_plist_content()
            with open(self._plist_path, 'w', encoding='utf-8') as f:
                f.write(plist_content)
            return True
        except Exception as e:
            print(f"Failed to enable macOS autostart: {e}")
            return False

    def disable(self) -> bool:
        try:
            if os.path.exists(self._plist_path):
                os.remove(self._plist_path)
            return True
        except Exception as e:
            print(f"Failed to disable macOS autostart: {e}")
            return False


class _LinuxAutoStart:
    def __init__(self, app_name: str):
        self._app_name = app_name
        self._autostart_dir = os.path.expanduser("~/.config/autostart")
        self._desktop_path = os.path.join(
            self._autostart_dir,
            f"{app_name.lower()}.desktop"
        )

    def _get_command(self) -> str:
        if getattr(sys, 'frozen', False):
            return sys.executable
        else:
            return f"{sys.executable} {os.path.abspath(sys.argv[0])}"

    def is_enabled(self) -> bool:
        return os.path.exists(self._desktop_path)

    def enable(self) -> bool:
        try:
            os.makedirs(self._autostart_dir, exist_ok=True)
            content = f"""[Desktop Entry]
Type=Application
Name={self._app_name}
Exec={self._get_command()}
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
"""
            with open(self._desktop_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"Failed to enable Linux autostart: {e}")
            return False

    def disable(self) -> bool:
        try:
            if os.path.exists(self._desktop_path):
                os.remove(self._desktop_path)
            return True
        except Exception as e:
            print(f"Failed to disable Linux autostart: {e}")
            return False
