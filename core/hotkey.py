import threading
from typing import Callable, Optional, Dict, Set
from utils.platform_utils import is_windows, is_macos


class HotkeyManager:
    def __init__(self):
        self._registered: Dict[str, Callable] = {}
        self._lock = threading.Lock()
        self._impl = self._create_impl()

    def _create_impl(self):
        if is_windows():
            return _KeyboardHotkeyImpl(self._registered, self._lock)
        else:
            return _PynputHotkeyImpl(self._registered, self._lock)

    def register(self, hotkey: str, callback: Callable[[], None]) -> bool:
        with self._lock:
            try:
                if hotkey in self._registered:
                    self.unregister(hotkey)
                self._registered[hotkey] = callback
                self._impl.register(hotkey, callback)
                return True
            except Exception as e:
                print(f"Failed to register hotkey {hotkey}: {e}")
                return False

    def unregister(self, hotkey: str) -> bool:
        with self._lock:
            try:
                if hotkey in self._registered:
                    self._impl.unregister(hotkey)
                    del self._registered[hotkey]
                return True
            except Exception:
                return False

    def unregister_all(self):
        with self._lock:
            for hotkey in list(self._registered.keys()):
                try:
                    self._impl.unregister(hotkey)
                except Exception:
                    pass
            self._registered.clear()

    def is_registered(self, hotkey: str) -> bool:
        return hotkey in self._registered


class _KeyboardHotkeyImpl:
    def __init__(self, registered: Dict[str, Callable], lock: threading.Lock):
        self._registered = registered
        self._lock = lock

    def register(self, hotkey: str, callback: Callable[[], None]):
        import keyboard
        keyboard.add_hotkey(hotkey, callback, suppress=False)

    def unregister(self, hotkey: str):
        import keyboard
        keyboard.remove_hotkey(hotkey)


class _PynputHotkeyImpl:
    def __init__(self, registered: Dict[str, Callable], lock: threading.Lock):
        self._registered = registered
        self._lock = lock
        self._listener = None
        self._current_keys: Set[str] = set()
        self._start_listener()

    def _parse_hotkey(self, hotkey: str) -> Set[str]:
        parts = hotkey.lower().replace(" ", "").split("+")
        normalized = set()
        for part in parts:
            if part in ("ctrl", "control", "cmd", "command"):
                normalized.add("ctrl")
            elif part in ("alt", "option"):
                normalized.add("alt")
            elif part in ("shift",):
                normalized.add("shift")
            elif part in ("win", "super", "meta"):
                normalized.add("cmd")
            else:
                key_map = {
                    "v": "v", "c": "c", "x": "x", "z": "z",
                    "a": "a", "s": "s", "q": "q", "w": "w",
                    "tab": "tab", "space": "space", "enter": "enter",
                    "esc": "esc", "escape": "esc",
                }
                normalized.add(key_map.get(part, part))
        return normalized

    def _key_to_str(self, key) -> str:
        try:
            from pynput import keyboard as kb
            if isinstance(key, kb.Key):
                name = key.name.lower()
                if name in ("cmd", "cmd_l", "cmd_r"):
                    return "cmd"
                elif name in ("ctrl", "ctrl_l", "ctrl_r"):
                    return "ctrl"
                elif name in ("alt", "alt_l", "alt_r", "alt_gr"):
                    return "alt"
                elif name in ("shift", "shift_l", "shift_r"):
                    return "shift"
                return name
            else:
                char = getattr(key, 'char', None)
                if char:
                    return char.lower()
                vk = getattr(key, 'vk', None)
                if vk:
                    return str(vk)
                return str(key).lower()
        except Exception:
            return ""

    def _on_press(self, key):
        key_str = self._key_to_str(key)
        if key_str:
            self._current_keys.add(key_str)
            self._check_hotkeys()

    def _on_release(self, key):
        key_str = self._key_to_str(key)
        if key_str:
            self._current_keys.discard(key_str)

    def _check_hotkeys(self):
        with self._lock:
            for hotkey_str, callback in list(self._registered.items()):
                expected = self._parse_hotkey(hotkey_str)
                if expected and expected.issubset(self._current_keys):
                    try:
                        threading.Thread(target=callback, daemon=True).start()
                    except Exception:
                        pass

    def _start_listener(self):
        try:
            from pynput import keyboard
            self._listener = keyboard.Listener(
                on_press=self._on_press,
                on_release=self._on_release
            )
            self._listener.daemon = True
            self._listener.start()
        except Exception as e:
            print(f"Failed to start pynput listener: {e}")

    def register(self, hotkey: str, callback: Callable[[], None]):
        pass

    def unregister(self, hotkey: str):
        pass
