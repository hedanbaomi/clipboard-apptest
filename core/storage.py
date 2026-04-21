import json
import os
import base64
from typing import List, Dict, Any, Optional
from datetime import datetime
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.helpers import generate_id, get_current_timestamp, truncate_text
from utils.content_type import ContentTypeDetector, ContentType
from core.clipboard_monitor import ClipboardData


class Storage:
    def __init__(self, data_dir: str, max_history: int = 100):
        self.data_dir = data_dir
        self.max_history = max_history
        self.history_file = os.path.join(data_dir, "clipboard_history.json")
        self.config_file = os.path.join(data_dir, "config.json")
        self._history: List[Dict[str, Any]] = []
        self._ensure_data_dir()
        self._load()
    
    def _ensure_data_dir(self):
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
    
    def _load(self):
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    self._history = json.load(f)
            except Exception:
                self._history = []
    
    def _save(self):
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self._history, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
    
    def add(self, content) -> Dict[str, Any]:
        if isinstance(content, ClipboardData):
            return self._add_clipboard_data(content)
        else:
            return self._add_text_content(str(content))
    
    def _add_text_content(self, content: str) -> Dict[str, Any]:
        content_type, type_label = ContentTypeDetector.detect(content)
        
        entry = {
            "id": generate_id(),
            "content": content,
            "type": content_type.value,
            "type_label": type_label,
            "icon": ContentTypeDetector.get_icon(content_type),
            "color": ContentTypeDetector.get_color(content_type),
            "preview": truncate_text(content, 80),
            "timestamp": get_current_timestamp(),
            "pinned": False
        }
        
        existing = self.find_by_content(content)
        if existing:
            self._history.remove(existing)
            entry["pinned"] = existing.get("pinned", False)
        
        self._history.insert(0, entry)
        self._cleanup_history()
        self._save()
        
        return entry
    
    def _add_clipboard_data(self, data: ClipboardData) -> Dict[str, Any]:
        if data.content_type == "image":
            return self._add_image(data)
        elif data.content_type == "file":
            return self._add_file(data)
        else:
            return self._add_text_content(data.text)
    
    def _add_image(self, data: ClipboardData) -> Dict[str, Any]:
        image_size = len(data.image_data)
        preview = f"[图片] {image_size // 1024}KB"
        
        entry = {
            "id": generate_id(),
            "type": "image",
            "type_label": "图片",
            "icon": "🖼️",
            "color": "#ff375f",
            "preview": preview,
            "timestamp": get_current_timestamp(),
            "pinned": False,
            "image_data": base64.b64encode(data.image_data).decode('utf-8'),
            "image_format": data.image_format
        }
        
        existing = self._find_by_image_data(data.image_data)
        if existing:
            self._history.remove(existing)
            entry["pinned"] = existing.get("pinned", False)
        
        self._history.insert(0, entry)
        self._cleanup_history()
        self._save()
        
        return entry
    
    def _add_file(self, data: ClipboardData) -> Dict[str, Any]:
        content = data.text
        content_type, type_label = ContentTypeDetector.detect(content)
        
        entry = {
            "id": generate_id(),
            "content": content,
            "type": "file",
            "type_label": "文件",
            "icon": "📁",
            "color": "#30d158",
            "preview": truncate_text(content, 80),
            "timestamp": get_current_timestamp(),
            "pinned": False,
            "files": data.files
        }
        
        existing = self.find_by_content(content)
        if existing:
            self._history.remove(existing)
            entry["pinned"] = existing.get("pinned", False)
        
        self._history.insert(0, entry)
        self._cleanup_history()
        self._save()
        
        return entry
    
    def _cleanup_history(self):
        unpinned = [e for e in self._history if not e.get("pinned", False)]
        pinned = [e for e in self._history if e.get("pinned", False)]
        
        if len(unpinned) > self.max_history:
            unpinned = unpinned[:self.max_history]
        
        self._history = pinned + unpinned
    
    def _find_by_image_data(self, image_data: bytes) -> Optional[Dict[str, Any]]:
        encoded = base64.b64encode(image_data).decode('utf-8')
        for entry in self._history:
            if entry.get("type") == "image" and entry.get("image_data") == encoded:
                return entry
        return None
    
    def remove(self, entry_id: str) -> bool:
        for i, entry in enumerate(self._history):
            if entry["id"] == entry_id:
                self._history.pop(i)
                self._save()
                return True
        return False
    
    def toggle_pin(self, entry_id: str) -> bool:
        for entry in self._history:
            if entry["id"] == entry_id:
                entry["pinned"] = not entry.get("pinned", False)
                self._save()
                return entry["pinned"]
        return False
    
    def clear(self, keep_pinned: bool = True):
        if keep_pinned:
            self._history = [e for e in self._history if e.get("pinned", False)]
        else:
            self._history = []
        self._save()
    
    def get_all(self) -> List[Dict[str, Any]]:
        return self._history.copy()
    
    def get_by_type(self, content_type: str) -> List[Dict[str, Any]]:
        return [e for e in self._history if e.get("type") == content_type]
    
    def search(self, query: str) -> List[Dict[str, Any]]:
        query = query.lower().strip()
        if not query:
            return self._history.copy()
        
        return [
            e for e in self._history
            if query in e.get("content", "").lower()
            or query in e.get("preview", "").lower()
        ]
    
    def find_by_content(self, content: str) -> Optional[Dict[str, Any]]:
        for entry in self._history:
            if entry.get("content") == content:
                return entry
        return None
    
    def get_by_id(self, entry_id: str) -> Optional[Dict[str, Any]]:
        for entry in self._history:
            if entry["id"] == entry_id:
                return entry
        return None
    
    def get_clipboard_data(self, entry_id: str) -> Optional[ClipboardData]:
        entry = self.get_by_id(entry_id)
        if not entry:
            return None
        
        content_type = entry.get("type", "text")
        
        if content_type == "image":
            image_data = base64.b64decode(entry.get("image_data", ""))
            return ClipboardData(
                content_type="image",
                image_data=image_data,
                image_format=entry.get("image_format", "png")
            )
        elif content_type == "file":
            return ClipboardData(
                content_type="file",
                files=entry.get("files", []),
                text=entry.get("content", "")
            )
        else:
            return ClipboardData(
                content_type="text",
                text=entry.get("content", "")
            )
