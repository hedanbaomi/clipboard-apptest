import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from gui.styles import AppleStyles, get_system_font


class SearchBar(tk.Frame):
    def __init__(self, parent: tk.Widget, styles: AppleStyles, 
                 on_search: Callable[[str], None],
                 on_theme_toggle: Callable[[], None],
                 on_settings: Callable[[], None]):
        super().__init__(parent, **styles.get_frame_style())
        self.styles = styles
        self.on_search = on_search
        self.on_theme_toggle = on_theme_toggle
        self.on_settings = on_settings
        
        self._create_widgets()
    
    def _get_font(self, base_size: int) -> str:
        size = max(8, int(base_size * self.styles.font_scale))
        return f"{get_system_font()} {size}"
    
    def _create_widgets(self):
        self.configure(bg=self.styles.colors.nav_bg)
        
        self._search_frame = tk.Frame(self, bg=self.styles.colors.bg_secondary)
        self._search_frame.pack(fill=tk.X, padx=self.styles.spacing["lg"], 
                                pady=self.styles.spacing["md"])
        
        self._search_icon = tk.Label(
            self._search_frame,
            text="🔍",
            font=self._get_font(14),
            bg=self.styles.colors.bg_secondary,
            fg=self.styles.colors.text_secondary
        )
        self._search_icon.pack(side=tk.LEFT, padx=(12, 6))
        
        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", self._on_search_change)
        
        self._search_entry = tk.Entry(
            self._search_frame,
            textvariable=self._search_var,
            font=self._get_font(14),
            **self.styles.get_entry_style()
        )
        self._search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=6, pady=10)
        self._search_entry.bind("<Escape>", lambda e: self._search_var.set(""))
        
        self._btn_frame = tk.Frame(self, bg=self.styles.colors.nav_bg)
        self._btn_frame.pack(side=tk.RIGHT, padx=self.styles.spacing["md"])
        
        self._theme_btn = tk.Label(
            self._btn_frame,
            text="🌙" if self.styles.theme == "light" else "☀️",
            font=self._get_font(18),
            bg=self.styles.colors.nav_bg,
            fg=self.styles.colors.text_primary,
            cursor="hand2"
        )
        self._theme_btn.pack(side=tk.LEFT, padx=6)
        self._theme_btn.bind("<Button-1>", lambda e: self.on_theme_toggle())
        
        self._settings_btn = tk.Label(
            self._btn_frame,
            text="⚙️",
            font=self._get_font(18),
            bg=self.styles.colors.nav_bg,
            fg=self.styles.colors.text_primary,
            cursor="hand2"
        )
        self._settings_btn.pack(side=tk.LEFT, padx=6)
        self._settings_btn.bind("<Button-1>", lambda e: self.on_settings())
    
    def _on_search_change(self, *args):
        query = self._search_var.get()
        self.on_search(query)
    
    def update_theme(self, styles: AppleStyles):
        self.styles = styles
        self.configure(bg=self.styles.colors.nav_bg)
        self._search_frame.configure(bg=self.styles.colors.bg_secondary)
        self._search_icon.configure(
            font=self._get_font(14),
            bg=self.styles.colors.bg_secondary,
            fg=self.styles.colors.text_secondary
        )
        self._search_entry.configure(
            font=self._get_font(14),
            bg=self.styles.colors.bg_secondary,
            fg=self.styles.colors.text_primary,
            insertbackground=self.styles.colors.text_primary
        )
        self._btn_frame.configure(bg=self.styles.colors.nav_bg)
        self._theme_btn.configure(
            text="🌙" if self.styles.theme == "light" else "☀️",
            font=self._get_font(18),
            bg=self.styles.colors.nav_bg,
            fg=self.styles.colors.text_primary
        )
        self._settings_btn.configure(
            font=self._get_font(18),
            bg=self.styles.colors.nav_bg,
            fg=self.styles.colors.text_primary
        )
    
    def clear(self):
        self._search_var.set("")
    
    def focus(self):
        self._search_entry.focus_set()
