import re
import os
from enum import Enum
from typing import Tuple

from utils.platform_utils import is_windows, is_macos


class ContentType(Enum):
    TEXT = "text"
    LINK = "link"
    FILE = "file"
    IMAGE = "image"
    CODE = "code"


class ContentTypeDetector:
    URL_PATTERN = re.compile(
        r'^(https?:\/\/)?([\da-z\.-]+)\.([a-z\.]{2,6})([\/\w \.-]*)*\/?$',
        re.IGNORECASE
    )
    WINDOWS_FILE_PATTERN = re.compile(
        r'^[a-zA-Z]:\\(?:[^\\/:*?"<>|\r\n]+\\)*[^\\/:*?"<>|\r\n]*$'
    )
    UNIX_FILE_PATTERN = re.compile(
        r'^/(?:[^/\0]+/)*[^/\0]*$'
    )
    CODE_PATTERNS = [
        re.compile(r'^\s*(def |class |import |from |function |const |let |var |public |private )', re.MULTILINE),
        re.compile(r'[{}\[\]();]+\s*$', re.MULTILINE),
        re.compile(r'^\s*<[^>]+>', re.MULTILINE),
    ]

    @classmethod
    def detect(cls, content: str) -> Tuple[ContentType, str]:
        if not content or not content.strip():
            return ContentType.TEXT, "文本"

        content = content.strip()

        if cls.URL_PATTERN.match(content):
            return ContentType.LINK, "链接"

        if cls._is_file_path(content):
            if os.path.exists(content):
                return ContentType.FILE, "文件"
            return ContentType.FILE, "路径"

        for pattern in cls.CODE_PATTERNS:
            if pattern.search(content):
                return ContentType.CODE, "代码"

        if len(content) > 200:
            return ContentType.TEXT, "长文本"

        return ContentType.TEXT, "文本"

    @classmethod
    def _is_file_path(cls, content: str) -> bool:
        if is_windows():
            return bool(cls.WINDOWS_FILE_PATTERN.match(content))
        else:
            return bool(cls.UNIX_FILE_PATTERN.match(content))

    @classmethod
    def get_icon(cls, content_type: ContentType) -> str:
        icons = {
            ContentType.TEXT: "📝",
            ContentType.LINK: "🔗",
            ContentType.FILE: "📁",
            ContentType.IMAGE: "🖼️",
            ContentType.CODE: "💻"
        }
        return icons.get(content_type, "📝")

    @classmethod
    def get_color(cls, content_type: ContentType) -> str:
        colors = {
            ContentType.TEXT: "#0071e3",
            ContentType.LINK: "#2997ff",
            ContentType.FILE: "#30d158",
            ContentType.IMAGE: "#ff375f",
            ContentType.CODE: "#bf5af2"
        }
        return colors.get(content_type, "#0071e3")
