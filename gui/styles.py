import tkinter as tk
from tkinter import ttk
from dataclasses import dataclass
from typing import Dict, Any

from utils.platform_utils import is_windows, is_macos


def get_system_font() -> str:
    if is_macos():
        return "Helvetica Neue"
    elif is_windows():
        return "SegoeUI"
    else:
        return "Noto Sans"


def enable_high_dpi():
    if is_windows():
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            try:
                import ctypes
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass
    elif is_macos():
        try:
            import subprocess
            subprocess.run(
                ['defaults', 'write', 'org.python.python',
                 'NSHighResolutionCapable', 'YES'],
                capture_output=True, timeout=2
            )
        except Exception:
            pass


@dataclass
class ColorPalette:
    bg_primary: str
    bg_secondary: str
    bg_card: str
    text_primary: str
    text_secondary: str
    accent: str
    link: str
    border: str
    shadow: str
    hover: str
    nav_bg: str


LIGHT_THEME = ColorPalette(
    bg_primary="#ffffff",
    bg_secondary="#f5f5f7",
    bg_card="#ffffff",
    text_primary="#1d1d1f",
    text_secondary="#6e6e73",
    accent="#0071e3",
    link="#0066cc",
    border="#d2d2d7",
    shadow="#d1d1d6",
    hover="#e8e8ed",
    nav_bg="#f5f5f7"
)

DARK_THEME = ColorPalette(
    bg_primary="#000000",
    bg_secondary="#1c1c1e",
    bg_card="#2c2c2e",
    text_primary="#ffffff",
    text_secondary="#98989d",
    accent="#0a84ff",
    link="#2997ff",
    border="#3a3a3c",
    shadow="#1c1c1e",
    hover="#3a3a3c",
    nav_bg="#1c1c1e"
)


BASE_TYPOGRAPHY = {
    "hero": {"size": 32, "weight": "bold"},
    "section": {"size": 22, "weight": "bold"},
    "card_title": {"size": 16, "weight": "bold"},
    "body": {"size": 14, "weight": "normal"},
    "caption": {"size": 12, "weight": "normal"},
    "micro": {"size": 11, "weight": "normal"}
}


SPACING = {
    "xs": 6,
    "sm": 10,
    "md": 16,
    "lg": 20,
    "xl": 28,
    "xxl": 36
}


BORDER_RADIUS = {
    "sm": 6,
    "md": 10,
    "lg": 14,
    "pill": 980,
    "circle": 50
}


class AppleStyles:
    def __init__(self, theme: str = "light", font_scale: float = 1.0):
        self.theme = theme
        self.font_scale = font_scale
        self.colors = LIGHT_THEME if theme == "light" else DARK_THEME
        self.typography = self._scale_typography(font_scale)
        self.spacing = SPACING
        self.radius = BORDER_RADIUS
        self._font_family = get_system_font()

    def _scale_typography(self, scale: float) -> Dict[str, Dict]:
        scaled = {}
        for key, value in BASE_TYPOGRAPHY.items():
            scaled[key] = {
                "size": max(8, int(value["size"] * scale)),
                "weight": value["weight"]
            }
        return scaled

    def set_font_scale(self, scale: float):
        self.font_scale = scale
        self.typography = self._scale_typography(scale)

    def switch_theme(self, theme: str):
        self.theme = theme
        self.colors = LIGHT_THEME if theme == "light" else DARK_THEME

    def get_font(self, style: str) -> str:
        t = self.typography.get(style, self.typography["body"])
        weight = "bold" if t["weight"] == "bold" else ""
        size = t["size"]
        if weight:
            return f"{self._font_family} {size} {weight}"
        return f"{self._font_family} {size}"

    def get_font_size(self, style: str) -> int:
        t = self.typography.get(style, self.typography["body"])
        return t["size"]

    def configure_root(self, root: tk.Tk):
        root.configure(bg=self.colors.bg_primary)
        base_size = max(8, int(14 * self.font_scale))
        root.option_add("*Font", f"{self._font_family} {base_size}")

    def get_frame_style(self) -> Dict[str, Any]:
        return {
            "bg": self.colors.bg_primary,
            "highlightthickness": 0
        }

    def get_card_style(self) -> Dict[str, Any]:
        return {
            "bg": self.colors.bg_card,
            "highlightthickness": 0,
            "padx": self.spacing["lg"],
            "pady": self.spacing["md"]
        }

    def get_button_style(self, primary: bool = True) -> Dict[str, Any]:
        if primary:
            return {
                "bg": self.colors.accent,
                "fg": "#ffffff",
                "activebackground": self.colors.accent,
                "activeforeground": "#ffffff",
                "relief": "flat",
                "cursor": "hand2",
                "padx": self.spacing["lg"],
                "pady": self.spacing["sm"]
            }
        else:
            return {
                "bg": self.colors.bg_secondary,
                "fg": self.colors.text_primary,
                "activebackground": self.colors.hover,
                "activeforeground": self.colors.text_primary,
                "relief": "flat",
                "cursor": "hand2",
                "padx": self.spacing["lg"],
                "pady": self.spacing["sm"]
            }

    def get_entry_style(self) -> Dict[str, Any]:
        return {
            "bg": self.colors.bg_secondary,
            "fg": self.colors.text_primary,
            "insertbackground": self.colors.text_primary,
            "relief": "flat",
            "highlightthickness": 1,
            "highlightcolor": self.colors.accent,
            "highlightbackground": self.colors.border
        }

    def get_label_style(self, style: str = "body") -> Dict[str, Any]:
        t = self.typography.get(style, self.typography["body"])
        return {
            "bg": self.colors.bg_primary,
            "fg": self.colors.text_primary,
            "font": self.get_font(style)
        }
