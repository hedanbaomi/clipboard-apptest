import platform
import sys
from typing import Optional


def get_platform() -> str:
    return platform.system()


def is_windows() -> bool:
    return get_platform() == "Windows"


def is_macos() -> bool:
    return get_platform() == "Darwin"


def is_linux() -> bool:
    return get_platform() == "Linux"


def get_app_name() -> str:
    return "AppleClipboard"


def get_data_dir() -> Optional[str]:
    if is_macos():
        return "~/Library/Application Support/AppleClipboard"
    elif is_windows():
        return None
    else:
        return "~/.config/AppleClipboard"


def get_python_command() -> str:
    return sys.executable


def get_script_path() -> str:
    import os
    return os.path.abspath(sys.argv[0])
