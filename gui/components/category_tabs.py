import tkinter as tk
from typing import Callable, List, Optional
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from gui.styles import AppleStyles, get_system_font
from utils.content_type import ContentType


CATEGORIES = [
    ("all", "全部", "📋"),
    ("text", "文本", "📝"),
    ("link", "链接", "🔗"),
    ("file", "文件", "📁"),
    ("image", "图片", "🖼️"),
    ("code", "代码", "💻"),
]


class CategoryTabs(tk.Frame):
    def __init__(self, parent: tk.Widget, styles: AppleStyles,
                 on_change: Callable[[str], None]):
        super().__init__(parent, **styles.get_frame_style())
        self.styles = styles
        self.on_change = on_change
        self._current_category = "all"
        self._buttons: dict = {}
        
        self._create_widgets()
    
    def _get_font(self, base_size: int) -> str:
        size = max(8, int(base_size * self.styles.font_scale))
        return f"{get_system_font()} {size}"
    
    def _create_widgets(self):
        self._container = tk.Frame(self, bg=self.styles.colors.bg_primary)
        self._container.pack(fill=tk.X, padx=self.styles.spacing["lg"], 
                             pady=self.styles.spacing["md"])
        
        for cat_id, cat_label, cat_icon in CATEGORIES:
            btn = self._create_tab(cat_id, cat_label, cat_icon)
            btn.pack(side=tk.LEFT, padx=4)
            self._buttons[cat_id] = btn
        
        self._update_button_states()
    
    def _create_tab(self, cat_id: str, label: str, icon: str) -> tk.Label:
        is_active = cat_id == self._current_category
        
        bg_color = self.styles.colors.accent if is_active else self.styles.colors.bg_secondary
        fg_color = "#ffffff" if is_active else self.styles.colors.text_primary
        
        btn = tk.Label(
            self._container,
            text=f"{icon} {label}",
            font=self._get_font(13),
            bg=bg_color,
            fg=fg_color,
            padx=self.styles.spacing["md"],
            pady=self.styles.spacing["sm"],
            cursor="hand2"
        )
        
        btn.bind("<Button-1>", lambda e, cid=cat_id: self._on_tab_click(cid))
        btn.bind("<Enter>", lambda e, b=btn, cid=cat_id: self._on_hover(b, cid))
        btn.bind("<Leave>", lambda e, b=btn, cid=cat_id: self._on_leave(b, cid))
        
        return btn
    
    def _on_tab_click(self, cat_id: str):
        if cat_id != self._current_category:
            self._current_category = cat_id
            self._update_button_states()
            self.on_change(cat_id)
    
    def _on_hover(self, btn: tk.Label, cat_id: str):
        if cat_id != self._current_category:
            btn.configure(bg=self.styles.colors.hover)
    
    def _on_leave(self, btn: tk.Label, cat_id: str):
        if cat_id != self._current_category:
            btn.configure(bg=self.styles.colors.bg_secondary)
    
    def _update_button_states(self):
        for cat_id, btn in self._buttons.items():
            is_active = cat_id == self._current_category
            bg_color = self.styles.colors.accent if is_active else self.styles.colors.bg_secondary
            fg_color = "#ffffff" if is_active else self.styles.colors.text_primary
            btn.configure(
                font=self._get_font(13),
                bg=bg_color, 
                fg=fg_color
            )
    
    def update_theme(self, styles: AppleStyles):
        self.styles = styles
        self.configure(bg=self.styles.colors.bg_primary)
        self._container.configure(bg=self.styles.colors.bg_primary)
        self._update_button_states()
    
    def get_current(self) -> str:
        return self._current_category
    
    def set_category(self, cat_id: str):
        if cat_id in self._buttons:
            self._current_category = cat_id
            self._update_button_states()
