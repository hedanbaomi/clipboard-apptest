import tkinter as tk
from typing import Callable, Dict, Any, Optional
import sys
import os
import base64
import io

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from gui.styles import AppleStyles, get_system_font
from utils.helpers import format_timestamp


class HistoryCard(tk.Frame):
    def __init__(self, parent: tk.Widget, styles: AppleStyles,
                 entry: Dict[str, Any],
                 on_copy: Callable[[str], None],
                 on_pin: Callable[[str], None],
                 on_delete: Callable[[str], None]):
        super().__init__(parent, bg=styles.colors.bg_card, padx=16, pady=14)
        self.styles = styles
        self.entry = entry
        self.on_copy = on_copy
        self.on_pin = on_pin
        self.on_delete = on_delete
        self._photo_image = None
        
        self._create_widgets()
        self._bind_events()
    
    def _get_font(self, base_size: int) -> str:
        size = max(8, int(base_size * self.styles.font_scale))
        return f"{get_system_font()} {size}"
    
    def _create_widgets(self):
        self._header = tk.Frame(self, bg=self.styles.colors.bg_card)
        self._header.pack(fill=tk.X)
        
        icon = self.entry.get("icon", "📝")
        type_label = self.entry.get("type_label", "文本")
        color = self.entry.get("color", self.styles.colors.accent)
        
        self._type_label = tk.Label(
            self._header,
            text=f"{icon} {type_label}",
            font=self._get_font(12),
            bg=self.styles.colors.bg_card,
            fg=color
        )
        self._type_label.pack(side=tk.LEFT)
        
        self._time_label = tk.Label(
            self._header,
            text=format_timestamp(self.entry.get("timestamp", "")),
            font=self._get_font(12),
            bg=self.styles.colors.bg_card,
            fg=self.styles.colors.text_secondary
        )
        self._time_label.pack(side=tk.RIGHT)
        
        self._content_frame = tk.Frame(self, bg=self.styles.colors.bg_card)
        self._content_frame.pack(fill=tk.X, pady=(10, 0))
        
        content_type = self.entry.get("type", "text")
        
        if content_type == "image":
            self._create_image_preview()
        else:
            preview = self.entry.get("preview", "")
            self._preview_label = tk.Label(
                self._content_frame,
                text=preview,
                font=self._get_font(14),
                bg=self.styles.colors.bg_card,
                fg=self.styles.colors.text_primary,
                anchor="w",
                justify=tk.LEFT,
                wraplength=420
            )
            self._preview_label.pack(fill=tk.X)
        
        self._action_frame = tk.Frame(self, bg=self.styles.colors.bg_card)
        self._action_frame.pack(fill=tk.X, pady=(12, 0))
        
        self._copy_btn = tk.Label(
            self._action_frame,
            text="📋 复制",
            font=self._get_font(12),
            bg=self.styles.colors.bg_secondary,
            fg=self.styles.colors.accent,
            padx=12,
            pady=4,
            cursor="hand2"
        )
        self._copy_btn.pack(side=tk.LEFT, padx=(0, 10))
        self._copy_btn.bind("<Button-1>", self._on_copy_click)
        
        pin_text = "📌 取消固定" if self.entry.get("pinned") else "📌 固定"
        self._pin_btn = tk.Label(
            self._action_frame,
            text=pin_text,
            font=self._get_font(12),
            bg=self.styles.colors.bg_secondary,
            fg=self.styles.colors.text_secondary,
            padx=12,
            pady=4,
            cursor="hand2"
        )
        self._pin_btn.pack(side=tk.LEFT, padx=(0, 10))
        self._pin_btn.bind("<Button-1>", self._on_pin_click)
        
        self._delete_btn = tk.Label(
            self._action_frame,
            text="🗑️ 删除",
            font=self._get_font(12),
            bg=self.styles.colors.bg_secondary,
            fg="#ff3b30",
            padx=12,
            pady=4,
            cursor="hand2"
        )
        self._delete_btn.pack(side=tk.LEFT)
        self._delete_btn.bind("<Button-1>", self._on_delete_click)
    
    def _create_image_preview(self):
        try:
            image_data_b64 = self.entry.get("image_data", "")
            if not image_data_b64:
                self._create_image_placeholder()
                return
            
            image_data = base64.b64decode(image_data_b64)
            
            from PIL import Image, ImageTk
            
            img = Image.open(io.BytesIO(image_data))
            
            max_width = 200
            max_height = 150
            
            img_width, img_height = img.size
            ratio = min(max_width / img_width, max_height / img_height)
            
            if ratio < 1:
                new_width = int(img_width * ratio)
                new_height = int(img_height * ratio)
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            self._photo_image = ImageTk.PhotoImage(img)
            
            self._image_label = tk.Label(
                self._content_frame,
                image=self._photo_image,
                bg=self.styles.colors.bg_card
            )
            self._image_label.pack(anchor="w")
            
            size_text = f"{img_width} x {img_height}"
            self._size_label = tk.Label(
                self._content_frame,
                text=size_text,
                font=self._get_font(10),
                bg=self.styles.colors.bg_card,
                fg=self.styles.colors.text_secondary
            )
            self._size_label.pack(anchor="w", pady=(4, 0))
            
        except Exception as e:
            print(f"Error creating image preview: {e}")
            self._create_image_placeholder()
    
    def _create_image_placeholder(self):
        preview = self.entry.get("preview", "[图片]")
        self._preview_label = tk.Label(
            self._content_frame,
            text=preview,
            font=self._get_font(14),
            bg=self.styles.colors.bg_card,
            fg=self.styles.colors.text_primary,
            anchor="w",
            justify=tk.LEFT
        )
        self._preview_label.pack(fill=tk.X)
    
    def _bind_events(self):
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        
        for child in self.winfo_children():
            self._bind_recursive(child)
    
    def _bind_recursive(self, widget):
        widget.bind("<Enter>", self._on_enter)
        widget.bind("<Leave>", self._on_leave)
        for child in widget.winfo_children():
            self._bind_recursive(child)
    
    def _on_enter(self, event=None):
        self.configure(bg=self.styles.colors.hover)
        self._update_bg(self.styles.colors.hover)
    
    def _on_leave(self, event=None):
        self.configure(bg=self.styles.colors.bg_card)
        self._update_bg(self.styles.colors.bg_card)
    
    def _update_bg(self, color: str):
        self._header.configure(bg=color)
        self._type_label.configure(bg=color)
        self._time_label.configure(bg=color)
        self._content_frame.configure(bg=color)
        
        if hasattr(self, '_preview_label'):
            self._preview_label.configure(bg=color)
        if hasattr(self, '_image_label'):
            self._image_label.configure(bg=color)
        if hasattr(self, '_size_label'):
            self._size_label.configure(bg=color)
        
        self._action_frame.configure(bg=color)
    
    def _on_copy_click(self, event=None):
        self.on_copy(self.entry.get("id", ""))
    
    def _on_pin_click(self, event=None):
        self.on_pin(self.entry.get("id", ""))
    
    def _on_delete_click(self, event=None):
        self.on_delete(self.entry.get("id", ""))
    
    def update_theme(self, styles: AppleStyles):
        self.styles = styles
        self.configure(bg=self.styles.colors.bg_card)
        self._update_bg(self.styles.colors.bg_card)
        
        self._type_label.configure(font=self._get_font(12))
        self._time_label.configure(
            font=self._get_font(12),
            fg=self.styles.colors.text_secondary
        )
        
        if hasattr(self, '_preview_label'):
            self._preview_label.configure(
                font=self._get_font(14),
                bg=self.styles.colors.bg_card,
                fg=self.styles.colors.text_primary
            )
        if hasattr(self, '_image_label'):
            self._image_label.configure(bg=self.styles.colors.bg_card)
        if hasattr(self, '_size_label'):
            self._size_label.configure(
                font=self._get_font(10),
                bg=self.styles.colors.bg_card,
                fg=self.styles.colors.text_secondary
            )
        
        self._copy_btn.configure(
            font=self._get_font(12),
            bg=self.styles.colors.bg_secondary,
            fg=self.styles.colors.accent
        )
        self._pin_btn.configure(
            font=self._get_font(12),
            bg=self.styles.colors.bg_secondary
        )
        self._delete_btn.configure(
            font=self._get_font(12),
            bg=self.styles.colors.bg_secondary
        )
    
    def set_wraplength(self, width: int):
        if hasattr(self, '_preview_label'):
            self._preview_label.configure(wraplength=max(200, width))
