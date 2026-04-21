import uuid
from datetime import datetime
from typing import Optional


def generate_id() -> str:
    return str(uuid.uuid4())[:8]


def truncate_text(text: str, max_length: int = 100) -> str:
    if not text:
        return ""
    text = text.strip().replace('\n', ' ').replace('\r', '')
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


def format_timestamp(timestamp: str) -> str:
    try:
        dt = datetime.fromisoformat(timestamp)
        now = datetime.now()
        diff = now - dt
        
        if diff.days > 0:
            return dt.strftime("%m/%d %H:%M")
        elif diff.seconds >= 3600:
            hours = diff.seconds // 3600
            return f"{hours}小时前"
        elif diff.seconds >= 60:
            minutes = diff.seconds // 60
            return f"{minutes}分钟前"
        else:
            return "刚刚"
    except Exception:
        return timestamp


def get_current_timestamp() -> str:
    return datetime.now().isoformat()
