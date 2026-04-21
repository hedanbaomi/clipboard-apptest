import tkinter as tk
from tkinter import messagebox
from typing import Dict, Any, List, Optional, Callable
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from gui.styles import AppleStyles, get_system_font
from gui.components.search_bar import SearchBar
from gui.components.category_tabs import CategoryTabs
from gui.components.history_card import HistoryCard
from gui.components.action_bar import ActionBar
from utils.content_type import ContentType
from utils.platform_utils import is_macos


class MainWindow:
    def __init__(self, config: Dict[str, Any], storage, clipboard_monitor, 
                 hotkey_manager, autostart):
        self.config = config
        self.storage = storage
        self.clipboard_monitor = clipboard_monitor
        self.hotkey_manager = hotkey_manager
        self.autostart = autostart
        
        font_scale = config.get("font_scale", 1.0)
        self.styles = AppleStyles(config.get("theme", "light"), font_scale)
        
        self._root: Optional[tk.Tk] = None
        self._cards: List[HistoryCard] = []
        self._current_filter = "all"
        self._search_query = ""
        self._is_visible = False
        self._on_close_callback: Optional[Callable] = None
    
    def create(self):
        self._root = tk.Tk()
        self._root.title("剪切板管理器")
        self._root.geometry(f"{self.config.get('window_width', 500)}x{self.config.get('window_height', 600)}")
        self._root.minsize(400, 400)
        
        self._root.overrideredirect(False)
        self._root.attributes("-toolwindow", False)
        
        self.styles.configure_root(self._root)
        
        self._root.protocol("WM_DELETE_WINDOW", self._on_close)
        self._root.bind("<Escape>", lambda e: self.hide())
        self._root.bind("<Configure>", self._on_window_resize)
        
        self._create_widgets()
        self._setup_hotkey()
        
        self._refresh_history()
    
    def _create_widgets(self):
        self._search_bar = SearchBar(
            self._root,
            self.styles,
            on_search=self._on_search,
            on_theme_toggle=self._toggle_theme,
            on_settings=self._show_settings
        )
        self._search_bar.pack(fill=tk.X)
        
        self._category_tabs = CategoryTabs(
            self._root,
            self.styles,
            on_change=self._on_category_change
        )
        self._category_tabs.pack(fill=tk.X)
        
        self._scroll_frame = tk.Frame(self._root, bg=self.styles.colors.bg_primary)
        self._scroll_frame.pack(fill=tk.BOTH, expand=True)
        
        self._canvas = tk.Canvas(
            self._scroll_frame,
            bg=self.styles.colors.bg_primary,
            highlightthickness=0
        )
        self._canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self._scrollbar = tk.Scrollbar(
            self._scroll_frame,
            orient=tk.VERTICAL,
            command=self._canvas.yview
        )
        self._scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self._canvas.configure(yscrollcommand=self._scrollbar.set)
        
        self._cards_frame = tk.Frame(self._canvas, bg=self.styles.colors.bg_primary)
        self._canvas_window = self._canvas.create_window((0, 0), window=self._cards_frame, anchor="nw")
        
        self._cards_frame.bind("<Configure>", self._on_frame_configure)
        self._canvas.bind("<Configure>", self._on_canvas_configure)
        
        self._canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self._canvas.bind_all("<Button-4>", self._on_mousewheel_linux)
        self._canvas.bind_all("<Button-5>", self._on_mousewheel_linux)
        
        self._empty_label = tk.Label(
            self._cards_frame,
            text="暂无剪切板记录\n复制内容后将自动保存",
            font=self._get_scaled_font(16),
            bg=self.styles.colors.bg_primary,
            fg=self.styles.colors.text_secondary,
            pady=100
        )
        
        self._action_bar = ActionBar(
            self._root,
            self.styles,
            on_clear=self._clear_history,
            on_settings=self._show_settings
        )
        self._action_bar.pack(fill=tk.X, side=tk.BOTTOM)
    
    def _get_scaled_font(self, base_size: int) -> str:
        size = max(8, int(base_size * self.styles.font_scale))
        return f"{get_system_font()} {size}"
    
    def _on_window_resize(self, event=None):
        if event and event.widget == self._root:
            self._update_cards_wraplength()
    
    def _update_cards_wraplength(self):
        if self._root:
            try:
                width = self._root.winfo_width() - 60
                for card in self._cards:
                    card.set_wraplength(width)
            except Exception:
                pass
    
    def _on_frame_configure(self, event=None):
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))
    
    def _on_canvas_configure(self, event=None):
        self._canvas.itemconfig(self._canvas_window, width=event.width)
    
    def _on_mousewheel(self, event):
        if is_macos():
            self._canvas.yview_scroll(int(-1 * event.delta), "units")
        else:
            self._canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_mousewheel_linux(self, event):
        if event.num == 4:
            self._canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self._canvas.yview_scroll(1, "units")
    
    def _setup_hotkey(self):
        hotkey = self.config.get("hotkey", "ctrl+shift+v")
        self.hotkey_manager.register(hotkey, self.toggle_visibility)
    
    def _on_search(self, query: str):
        self._search_query = query
        self._refresh_history()
    
    def _on_category_change(self, category: str):
        self._current_filter = category
        self._refresh_history()
    
    def _toggle_theme(self):
        new_theme = "dark" if self.styles.theme == "light" else "light"
        self.styles.switch_theme(new_theme)
        self.config["theme"] = new_theme
        self._save_config()
        
        self._apply_styles()
    
    def _apply_styles(self):
        self.styles.configure_root(self._root)
        self._root.configure(bg=self.styles.colors.bg_primary)
        
        self._search_bar.update_theme(self.styles)
        self._category_tabs.update_theme(self.styles)
        self._scroll_frame.configure(bg=self.styles.colors.bg_primary)
        self._canvas.configure(bg=self.styles.colors.bg_primary)
        self._cards_frame.configure(bg=self.styles.colors.bg_primary)
        self._empty_label.configure(
            font=self._get_scaled_font(16),
            bg=self.styles.colors.bg_primary,
            fg=self.styles.colors.text_secondary
        )
        self._action_bar.update_theme(self.styles)
        
        for card in self._cards:
            card.update_theme(self.styles)
    
    def _refresh_history(self):
        for card in self._cards:
            card.destroy()
        self._cards.clear()
        
        entries = self.storage.get_all()
        
        if self._search_query:
            entries = self.storage.search(self._search_query)
        
        if self._current_filter != "all":
            entries = [e for e in entries if e.get("type") == self._current_filter]
        
        if not entries:
            self._empty_label.pack(pady=50)
            return
        
        self._empty_label.pack_forget()
        
        for entry in entries:
            card = HistoryCard(
                self._cards_frame,
                self.styles,
                entry,
                on_copy=self._copy_to_clipboard,
                on_pin=self._toggle_pin,
                on_delete=self._delete_entry
            )
            card.pack(fill=tk.X, padx=self.styles.spacing["md"], pady=self.styles.spacing["xs"])
            self._cards.append(card)
        
        self._root.after(100, self._update_cards_wraplength)
    
    def _copy_to_clipboard(self, entry_id: str):
        clipboard_data = self.storage.get_clipboard_data(entry_id)
        if clipboard_data:
            self.clipboard_monitor.set_clipboard(clipboard_data)
            self._show_toast("已复制到剪切板")
        else:
            entry = self.storage.get_by_id(entry_id)
            if entry:
                content = entry.get("content", "")
                self.clipboard_monitor.set_clipboard(content)
                self._show_toast("已复制到剪切板")
    
    def _toggle_pin(self, entry_id: str):
        pinned = self.storage.toggle_pin(entry_id)
        self._refresh_history()
        msg = "已固定" if pinned else "已取消固定"
        self._show_toast(msg)
    
    def _delete_entry(self, entry_id: str):
        self.storage.remove(entry_id)
        self._refresh_history()
        self._show_toast("已删除")
    
    def _clear_history(self):
        if messagebox.askyesno("确认", "确定要清空所有历史记录吗？（固定内容将保留）"):
            self.storage.clear(keep_pinned=True)
            self._refresh_history()
            self._show_toast("已清空历史")
    
    def _show_settings(self):
        settings_window = tk.Toplevel(self._root)
        settings_window.title("设置")
        settings_window.geometry("450x400")
        settings_window.resizable(False, False)
        settings_window.configure(bg=self.styles.colors.bg_primary)
        settings_window.transient(self._root)
        settings_window.grab_set()
        
        title = tk.Label(
            settings_window,
            text="⚙️ 设置",
            font=self._get_scaled_font(20) + " bold",
            bg=self.styles.colors.bg_primary,
            fg=self.styles.colors.text_primary
        )
        title.pack(pady=20)
        
        font_frame = tk.LabelFrame(
            settings_window,
            text=" 字体大小 ",
            font=self._get_scaled_font(12),
            bg=self.styles.colors.bg_primary,
            fg=self.styles.colors.text_primary,
            padx=20,
            pady=10
        )
        font_frame.pack(fill=tk.X, padx=20, pady=10)
        
        font_scale = self.config.get("font_scale", 1.0)
        self._font_scale_var = tk.DoubleVar(value=font_scale)
        
        font_label_frame = tk.Frame(font_frame, bg=self.styles.colors.bg_primary)
        font_label_frame.pack(fill=tk.X)
        
        font_label = tk.Label(
            font_label_frame,
            text=f"缩放比例: {int(font_scale * 100)}%",
            font=self._get_scaled_font(12),
            bg=self.styles.colors.bg_primary,
            fg=self.styles.colors.text_primary
        )
        font_label.pack(side=tk.LEFT)
        
        font_preview = tk.Label(
            font_label_frame,
            text="预览文本 Preview",
            font=self._get_scaled_font(14),
            bg=self.styles.colors.bg_primary,
            fg=self.styles.colors.text_secondary
        )
        font_preview.pack(side=tk.RIGHT)
        
        font_slider = tk.Scale(
            font_frame,
            from_=0.7,
            to=1.5,
            resolution=0.1,
            orient=tk.HORIZONTAL,
            variable=self._font_scale_var,
            bg=self.styles.colors.bg_primary,
            fg=self.styles.colors.text_primary,
            highlightthickness=0,
            troughcolor=self.styles.colors.bg_secondary,
            activebackground=self.styles.colors.accent,
            length=380,
            showvalue=False,
            command=lambda v: self._on_font_scale_change(float(v), font_label, font_preview)
        )
        font_slider.pack(fill=tk.X, pady=5)
        
        autostart_frame = tk.Frame(settings_window, bg=self.styles.colors.bg_primary)
        autostart_frame.pack(fill=tk.X, padx=20, pady=10)
        
        autostart_label = tk.Label(
            autostart_frame,
            text="开机自启动",
            font=self._get_scaled_font(12),
            bg=self.styles.colors.bg_primary,
            fg=self.styles.colors.text_primary
        )
        autostart_label.pack(side=tk.LEFT)
        
        autostart_var = tk.BooleanVar(value=self.autostart.is_enabled())
        autostart_check = tk.Checkbutton(
            autostart_frame,
            variable=autostart_var,
            bg=self.styles.colors.bg_primary,
            activebackground=self.styles.colors.bg_primary,
            selectcolor=self.styles.colors.bg_secondary,
            command=lambda: self._toggle_autostart(autostart_var.get())
        )
        autostart_check.pack(side=tk.RIGHT)
        
        hotkey_frame = tk.Frame(settings_window, bg=self.styles.colors.bg_primary)
        hotkey_frame.pack(fill=tk.X, padx=20, pady=10)
        
        hotkey_label = tk.Label(
            hotkey_frame,
            text=f"快捷键: {self.config.get('hotkey', 'ctrl+shift+v').upper()}",
            font=self._get_scaled_font(12),
            bg=self.styles.colors.bg_primary,
            fg=self.styles.colors.text_secondary
        )
        hotkey_label.pack(side=tk.LEFT)
        
        info_label = tk.Label(
            settings_window,
            text="按 ESC 或关闭窗口退出设置",
            font=self._get_scaled_font(10),
            bg=self.styles.colors.bg_primary,
            fg=self.styles.colors.text_secondary
        )
        info_label.pack(side=tk.BOTTOM, pady=20)
    
    def _on_font_scale_change(self, scale: float, label: tk.Label, preview: tk.Label):
        label.configure(text=f"缩放比例: {int(scale * 100)}%")
        preview.configure(font=self._get_scaled_font(14))
        
        self.styles.set_font_scale(scale)
        self.config["font_scale"] = scale
        self._save_config()
        
        self._apply_styles()
        self._refresh_history()
    
    def _toggle_autostart(self, enabled: bool):
        if enabled:
            self.autostart.enable()
            self._show_toast("已开启开机自启")
        else:
            self.autostart.disable()
            self._show_toast("已关闭开机自启")
    
    def _show_toast(self, message: str):
        toast = tk.Toplevel(self._root)
        toast.overrideredirect(True)
        toast.attributes("-topmost", True)
        
        label = tk.Label(
            toast,
            text=message,
            font=self._get_scaled_font(12),
            bg=self.styles.colors.accent,
            fg="#ffffff",
            padx=20,
            pady=10
        )
        label.pack()
        
        toast.update_idletasks()
        x = self._root.winfo_x() + (self._root.winfo_width() - toast.winfo_width()) // 2
        y = self._root.winfo_y() + 50
        toast.geometry(f"+{x}+{y}")
        
        self._root.after(2000, toast.destroy)
    
    def _save_config(self):
        try:
            config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.json")
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4)
        except Exception:
            pass
    
    def _on_close(self):
        self.hide()
    
    def on_clipboard_change(self, content):
        self.storage.add(content)
        if self._root:
            try:
                self._root.after(0, self._refresh_history)
            except Exception:
                pass
    
    def show(self):
        if self._root:
            self._root.deiconify()
            self._root.lift()
            self._root.focus_force()
            self._search_bar.focus()
            self._is_visible = True
    
    def hide(self):
        if self._root:
            self._root.withdraw()
            self._is_visible = False
    
    def toggle_visibility(self):
        if self._is_visible:
            self.hide()
        else:
            self.show()
    
    def run(self):
        if self._root:
            self._root.mainloop()
    
    def set_on_close(self, callback: Callable):
        self._on_close_callback = callback
