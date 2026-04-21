import tkinter as tk
from typing import Callable
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from gui.styles import AppleStyles, get_system_font


class ActionBar(tk.Frame):
    def __init__(self, parent: tk.Widget, styles: AppleStyles,
                 on_clear: Callable[[], None],
                 on_settings: Callable[[], None]):
        super().__init__(parent, **styles.get_frame_style())
        self.styles = styles
        self.on_clear = on_clear
        self.on_settings = on_settings
        
        self._create_widgets()
    
    def _get_font(self, base_size: int) -> str:
        size = max(8, int(base_size * self.styles.font_scale))
        return f"{get_system_font()} {size}"
    
    def _create_widgets(self):
        self.configure(bg=self.styles.colors.bg_secondary)
        
        self._container = tk.Frame(self, bg=self.styles.colors.bg_secondary)
        self._container.pack(fill=tk.X, padx=self.styles.spacing["lg"], 
                             pady=self.styles.spacing["md"])
        
        self._clear_btn = tk.Label(
            self._container,
            text="🗑️ 清空历史",
            font=self._get_font(13),
            bg=self.styles.colors.bg_primary,
            fg="#ff3b30",
            padx=self.styles.spacing["lg"],
            pady=self.styles.spacing["sm"],
            cursor="hand2"
        )
        self._clear_btn.pack(side=tk.LEFT, padx=6)
        self._clear_btn.bind("<Button-1>", lambda e: self.on_clear())
        self._clear_btn.bind("<Enter>", lambda e: self._clear_btn.configure(bg=self.styles.colors.hover))
        self._clear_btn.bind("<Leave>", lambda e: self._clear_btn.configure(bg=self.styles.colors.bg_primary))
        
        self._settings_btn = tk.Label(
            self._container,
            text="⚙️ 设置",
            font=self._get_font(13),
            bg=self.styles.colors.bg_primary,
            fg=self.styles.colors.text_primary,
            padx=self.styles.spacing["lg"],
            pady=self.styles.spacing["sm"],
            cursor="hand2"
        )
        self._settings_btn.pack(side=tk.RIGHT, padx=6)
        self._settings_btn.bind("<Button-1>", lambda e: self.on_settings())
        self._settings_btn.bind("<Enter>", lambda e: self._settings_btn.configure(bg=self.styles.colors.hover))
        self._settings_btn.bind("<Leave>", lambda e: self._settings_btn.configure(bg=self.styles.colors.bg_primary))
    
    def update_theme(self, styles: AppleStyles):
        self.styles = styles
        self.configure(bg=self.styles.colors.bg_secondary)
        self._container.configure(bg=self.styles.colors.bg_secondary)
        self._clear_btn.configure(
            font=self._get_font(13),
            bg=self.styles.colors.bg_primary,
            fg="#ff3b30"
        )
        self._settings_btn.configure(
            font=self._get_font(13),
            bg=self.styles.colors.bg_primary,
            fg=self.styles.colors.text_primary
        )
