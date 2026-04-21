import threading
import time
import os
import base64
import io
import subprocess
import tempfile
from typing import Callable, Optional, List
from abc import ABC, abstractmethod

import pyperclip

from utils.platform_utils import is_windows, is_macos


class ClipboardData:
    def __init__(self, content_type: str = "text", text: str = "",
                 image_data: bytes = b"", image_format: str = "png",
                 files: List[str] = None):
        self.content_type = content_type
        self.text = text
        self.image_data = image_data
        self.image_format = image_format
        self.files = files or []

    def to_dict(self) -> dict:
        result = {"type": self.content_type}
        if self.content_type == "image":
            result["image_data"] = base64.b64encode(self.image_data).decode('utf-8')
            result["image_format"] = self.image_format
        elif self.content_type == "file":
            result["files"] = self.files
            result["text"] = self.text
        else:
            result["text"] = self.text
        return result

    @classmethod
    def from_dict(cls, data: dict) -> 'ClipboardData':
        content_type = data.get("type", "text")
        if content_type == "image":
            image_data = base64.b64decode(data.get("image_data", ""))
            return cls(content_type=content_type, image_data=image_data,
                       image_format=data.get("image_format", "png"))
        elif content_type == "file":
            return cls(content_type=content_type, files=data.get("files", []),
                       text=data.get("text", ""))
        else:
            return cls(content_type=content_type, text=data.get("text", ""))


class ClipboardBackend(ABC):
    @abstractmethod
    def get_content(self) -> Optional[ClipboardData]:
        pass

    @abstractmethod
    def set_content(self, data: ClipboardData) -> bool:
        pass


class WindowsClipboardBackend(ClipboardBackend):
    def __init__(self):
        import ctypes
        from ctypes import wintypes

        self.CF_UNICODETEXT = 13
        self.CF_HDROP = 15
        self.CF_DIB = 8
        self.CF_DIBV5 = 17
        self.GHND = 0x0002

        self.user32 = ctypes.windll.user32
        self.kernel32 = ctypes.windll.kernel32
        self.shell32 = ctypes.windll.shell32
        self.gdi32 = ctypes.windll.gdi32
        self.wintypes = wintypes
        self.ctypes = ctypes

        self._setup_api()

    def _setup_api(self):
        ct = self.ctypes
        wt = self.wintypes
        u = self.user32
        k = self.kernel32
        s = self.shell32
        g = self.gdi32

        u.OpenClipboard.argtypes = [wt.HWND]
        u.OpenClipboard.restype = wt.BOOL
        u.CloseClipboard.argtypes = []
        u.CloseClipboard.restype = wt.BOOL
        u.GetClipboardData.argtypes = [wt.UINT]
        u.GetClipboardData.restype = wt.HANDLE
        u.SetClipboardData.argtypes = [wt.UINT, wt.HANDLE]
        u.SetClipboardData.restype = wt.HANDLE
        u.EmptyClipboard.argtypes = []
        u.EmptyClipboard.restype = wt.BOOL
        u.IsClipboardFormatAvailable.argtypes = [wt.UINT]
        u.IsClipboardFormatAvailable.restype = wt.BOOL

        s.DragQueryFileW.argtypes = [ct.c_void_p, wt.UINT, wt.LPWSTR, wt.UINT]
        s.DragQueryFileW.restype = wt.UINT

        k.GlobalAlloc.argtypes = [wt.UINT, ct.c_size_t]
        k.GlobalAlloc.restype = wt.HGLOBAL
        k.GlobalLock.argtypes = [wt.HGLOBAL]
        k.GlobalLock.restype = wt.LPVOID
        k.GlobalUnlock.argtypes = [wt.HGLOBAL]
        k.GlobalUnlock.restype = wt.BOOL
        k.GlobalFree.argtypes = [wt.HGLOBAL]
        k.GlobalFree.restype = wt.HGLOBAL
        k.GlobalSize.argtypes = [wt.HGLOBAL]
        k.GlobalSize.restype = ct.c_size_t

    def get_content(self) -> Optional[ClipboardData]:
        try:
            has_files = self.user32.IsClipboardFormatAvailable(self.CF_HDROP)
            has_image = (self.user32.IsClipboardFormatAvailable(self.CF_DIB) or
                         self.user32.IsClipboardFormatAvailable(self.CF_DIBV5))
            has_text = self.user32.IsClipboardFormatAvailable(self.CF_UNICODETEXT)

            if has_files:
                files = self._get_files()
                if files:
                    return ClipboardData(content_type="file", files=files,
                                         text="\n".join(files))

            if has_image and not has_text:
                image_data = self._get_image()
                if image_data:
                    return ClipboardData(content_type="image", image_data=image_data)

            if has_text:
                content = pyperclip.paste()
                if content:
                    return ClipboardData(content_type="text", text=content)

            if has_image:
                image_data = self._get_image()
                if image_data:
                    return ClipboardData(content_type="image", image_data=image_data)

            try:
                content = pyperclip.paste()
                if content:
                    return ClipboardData(content_type="text", text=content)
            except Exception:
                pass

            return None
        except Exception as e:
            print(f"Error getting clipboard: {e}")
            return None

    def _get_files(self) -> Optional[List[str]]:
        try:
            if not self.user32.OpenClipboard(None):
                return None
            try:
                h_drop = self.user32.GetClipboardData(self.CF_HDROP)
                if not h_drop:
                    return None
                file_count = self.shell32.DragQueryFileW(h_drop, 0xFFFFFFFF, None, 0)
                if file_count == 0:
                    return None
                files = []
                for i in range(file_count):
                    buf = self.ctypes.create_unicode_buffer(260)
                    self.shell32.DragQueryFileW(h_drop, i, buf, 260)
                    files.append(buf.value)
                return files
            finally:
                self.user32.CloseClipboard()
        except Exception as e:
            print(f"Error getting files: {e}")
            return None

    def _get_image(self) -> Optional[bytes]:
        try:
            if not self.user32.OpenClipboard(None):
                return None
            try:
                h_data = self.user32.GetClipboardData(self.CF_DIB)
                if not h_data:
                    h_data = self.user32.GetClipboardData(self.CF_DIBV5)
                if not h_data:
                    return None
                size = self.kernel32.GlobalSize(h_data)
                if size == 0:
                    return None
                p_data = self.kernel32.GlobalLock(h_data)
                if not p_data:
                    return None
                try:
                    dib_data = self.ctypes.string_at(p_data, size)
                    return self._dib_to_png(dib_data)
                finally:
                    self.kernel32.GlobalUnlock(h_data)
            finally:
                self.user32.CloseClipboard()
        except Exception as e:
            print(f"Error getting image: {e}")
            return None

    def _dib_to_png(self, dib_data: bytes) -> bytes:
        try:
            class BITMAPINFOHEADER(self.ctypes.Structure):
                _fields_ = [
                    ("biSize", self.wintypes.DWORD),
                    ("biWidth", self.wintypes.LONG),
                    ("biHeight", self.wintypes.LONG),
                    ("biPlanes", self.wintypes.WORD),
                    ("biBitCount", self.wintypes.WORD),
                    ("biCompression", self.wintypes.DWORD),
                    ("biSizeImage", self.wintypes.DWORD),
                    ("biXPelsPerMeter", self.wintypes.LONG),
                    ("biYPelsPerMeter", self.wintypes.LONG),
                    ("biClrUsed", self.wintypes.DWORD),
                    ("biClrImportant", self.wintypes.DWORD),
                ]

            header = BITMAPINFOHEADER.from_buffer_copy(dib_data[:40])
            width = header.biWidth
            height = header.biHeight
            bit_count = header.biBitCount
            top_down = height < 0
            if top_down:
                height = -height

            row_size = ((width * bit_count + 31) // 32) * 4
            pixel_data_size = row_size * height

            if bit_count == 32:
                pixels = dib_data[40:40 + pixel_data_size]
            elif bit_count == 24:
                pixels = dib_data[40:40 + pixel_data_size]
            else:
                return b""

            from PIL import Image
            if bit_count == 32:
                img = Image.frombytes('RGBA', (width, height), pixels, 'raw', 'BGRA')
            else:
                img = Image.frombytes('RGB', (width, height), pixels, 'raw', 'BGR')

            if not top_down:
                img = img.transpose(Image.FLIP_TOP_BOTTOM)

            output = io.BytesIO()
            img.save(output, format='PNG')
            return output.getvalue()
        except Exception as e:
            print(f"Error converting DIB to PNG: {e}")
            return b""

    def set_content(self, data: ClipboardData) -> bool:
        try:
            if data.content_type == "image":
                return self._set_image(data.image_data)
            elif data.content_type == "file":
                return self._set_files(data.files)
            else:
                text = data.text
                if self._is_file_path(text):
                    files = self._get_file_paths(text)
                    if files:
                        return self._set_files(files)
                pyperclip.copy(text)
                return True
        except Exception as e:
            print(f"Error setting clipboard: {e}")
            return False

    def _is_file_path(self, content: str) -> bool:
        if not content:
            return False
        lines = content.strip().split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if not os.path.exists(line):
                return False
        return len(lines) > 0

    def _get_file_paths(self, content: str) -> List[str]:
        lines = content.strip().split('\n')
        return [l.strip() for l in lines if l.strip() and os.path.exists(l.strip())]

    def _set_files(self, files: List[str]) -> bool:
        try:
            ct = self.ctypes
            wt = self.wintypes

            class DROPFILES(ct.Structure):
                _fields_ = [
                    ("pFiles", wt.DWORD),
                    ("pt", wt.POINT),
                    ("fNC", wt.BOOL),
                    ("fWide", wt.BOOL),
                ]

            total_size = ct.sizeof(DROPFILES)
            for f in files:
                total_size += (len(f) + 1) * 2
            total_size += 2

            h_global = self.kernel32.GlobalAlloc(self.GHND, total_size)
            if not h_global:
                return False

            p_global = self.kernel32.GlobalLock(h_global)
            if not p_global:
                self.kernel32.GlobalFree(h_global)
                return False

            try:
                dropfiles = DROPFILES()
                dropfiles.pFiles = ct.sizeof(DROPFILES)
                dropfiles.fWide = True
                ct.memmove(p_global, ct.byref(dropfiles), ct.sizeof(DROPFILES))

                offset = ct.sizeof(DROPFILES)
                for f in files:
                    file_bytes = (f + '\0').encode('utf-16-le')
                    ct.memmove(p_global + offset, file_bytes, len(file_bytes))
                    offset += len(file_bytes)
                ct.memset(p_global + offset, 0, 2)
            finally:
                self.kernel32.GlobalUnlock(h_global)

            if not self.user32.OpenClipboard(None):
                self.kernel32.GlobalFree(h_global)
                return False
            try:
                self.user32.EmptyClipboard()
                if not self.user32.SetClipboardData(self.CF_HDROP, h_global):
                    self.kernel32.GlobalFree(h_global)
                    return False
            finally:
                self.user32.CloseClipboard()
            return True
        except Exception as e:
            print(f"Error setting files: {e}")
            return False

    def _set_image(self, image_data: bytes) -> bool:
        try:
            from PIL import Image

            img = Image.open(io.BytesIO(image_data))
            if img.mode != 'RGBA':
                img = img.convert('RGBA')

            width, height = img.size

            class BITMAPINFOHEADER(ct.Structure):
                _fields_ = [
                    ("biSize", self.wintypes.DWORD),
                    ("biWidth", self.wintypes.LONG),
                    ("biHeight", self.wintypes.LONG),
                    ("biPlanes", self.wintypes.WORD),
                    ("biBitCount", self.wintypes.WORD),
                    ("biCompression", self.wintypes.DWORD),
                    ("biSizeImage", self.wintypes.DWORD),
                    ("biXPelsPerMeter", self.wintypes.LONG),
                    ("biYPelsPerMeter", self.wintypes.LONG),
                    ("biClrUsed", self.wintypes.DWORD),
                    ("biClrImportant", self.wintypes.DWORD),
                ]

            class BITMAPINFO(ct.Structure):
                _fields_ = [
                    ("bmiHeader", BITMAPINFOHEADER),
                    ("bmiColors", self.wintypes.DWORD * 3),
                ]

            bmi = BITMAPINFO()
            bmi.bmiHeader.biSize = ct.sizeof(BITMAPINFOHEADER)
            bmi.bmiHeader.biWidth = width
            bmi.bmiHeader.biHeight = height
            bmi.bmiHeader.biPlanes = 1
            bmi.bmiHeader.biBitCount = 32
            bmi.bmiHeader.biCompression = 0
            bmi.bmiHeader.biSizeImage = width * height * 4

            hdc = self.gdi32.CreateCompatibleDC(None)
            if not hdc:
                return False

            p_bits = self.wintypes.LPVOID()
            h_bitmap = self.gdi32.CreateDIBSection(
                hdc, self.ctypes.byref(bmi), 0,
                self.ctypes.byref(p_bits), None, 0
            )

            if not h_bitmap or not p_bits:
                self.gdi32.DeleteDC(hdc)
                return False

            pixels = img.tobytes('raw', 'BGRA')
            self.ctypes.memmove(p_bits, pixels, len(pixels))
            self.gdi32.DeleteDC(hdc)

            if not self.user32.OpenClipboard(None):
                self.gdi32.DeleteObject(h_bitmap)
                return False
            try:
                self.user32.EmptyClipboard()
                result = self.user32.SetClipboardData(2, h_bitmap)
                if not result:
                    self.gdi32.DeleteObject(h_bitmap)
                    return False
            finally:
                self.user32.CloseClipboard()
            return True
        except Exception as e:
            print(f"Error setting image: {e}")
            return False


class MacOSClipboardBackend(ClipboardBackend):
    def get_content(self) -> Optional[ClipboardData]:
        try:
            image_data = self._get_image()
            if image_data:
                return ClipboardData(content_type="image", image_data=image_data)

            files = self._get_files()
            if files:
                return ClipboardData(content_type="file", files=files,
                                     text="\n".join(files))

            content = pyperclip.paste()
            if content:
                return ClipboardData(content_type="text", text=content)

            return None
        except Exception as e:
            print(f"Error getting clipboard: {e}")
            return None

    def _get_image(self) -> Optional[bytes]:
        try:
            result = subprocess.run(
                ['osascript', '-e', 'clipboard info'],
                capture_output=True, text=True, timeout=2
            )
            if 'class furl' in result.stdout.lower() or 'class pngf' in result.stdout.lower() or 'class JPEG' in result.stdout.lower() or 'class TIFF' in result.stdout.lower() or 'class PICT' in result.stdout.lower() or '«class PNGf»' in result.stdout or '«class TIFF»' in result.stdout:
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                    tmp_path = tmp.name

                try:
                    subprocess.run(
                        ['osascript', '-e',
                         f'set theType to (clipboard info) as text\n'
                         f'set theClip to the clipboard as «class PNGf»\n'
                         f'set fp to open for access POSIX file "{tmp_path}" with write permission\n'
                         f'write theClip to fp\n'
                         f'close access fp'],
                        capture_output=True, timeout=5
                    )

                    if os.path.exists(tmp_path) and os.path.getsize(tmp_path) > 0:
                        with open(tmp_path, 'rb') as f:
                            return f.read()
                except Exception:
                    pass
                finally:
                    try:
                        os.unlink(tmp_path)
                    except Exception:
                        pass

            return None
        except Exception as e:
            print(f"Error getting macOS image: {e}")
            return None

    def _get_files(self) -> Optional[List[str]]:
        try:
            result = subprocess.run(
                ['osascript', '-e',
                 'set theClip to the clipboard as «class furl»\n'
                 'return POSIX path of theClip'],
                capture_output=True, text=True, timeout=2
            )
            if result.returncode == 0 and result.stdout.strip():
                path = result.stdout.strip()
                if os.path.exists(path):
                    return [path]

            result = subprocess.run(
                ['osascript', '-e',
                 'try\n'
                 '  set thePaths to {}\n'
                 '  set theClip to the clipboard as alias list\n'
                 '  repeat with anAlias in theClip\n'
                 '    set end of thePaths to POSIX path of anAlias\n'
                 '  end repeat\n'
                 '  return thePaths\n'
                 'on error\n'
                 '  return ""\n'
                 'end try'],
                capture_output=True, text=True, timeout=2
            )
            if result.returncode == 0 and result.stdout.strip():
                paths = [p.strip() for p in result.stdout.strip().split(',')]
                valid = [p for p in paths if p and os.path.exists(p)]
                if valid:
                    return valid

            return None
        except Exception:
            return None

    def set_content(self, data: ClipboardData) -> bool:
        try:
            if data.content_type == "image":
                return self._set_image(data.image_data)
            elif data.content_type == "file":
                return self._set_files(data.files)
            else:
                pyperclip.copy(data.text)
                return True
        except Exception as e:
            print(f"Error setting clipboard: {e}")
            return False

    def _set_image(self, image_data: bytes) -> bool:
        try:
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                tmp_path = tmp.name
                tmp.write(image_data)

            try:
                subprocess.run(
                    ['osascript', '-e',
                     f'set theImage to read (POSIX file "{tmp_path}") as «class PNGf»\n'
                     f'set the clipboard to theImage'],
                    capture_output=True, timeout=5
                )
                return True
            finally:
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass
        except Exception as e:
            print(f"Error setting macOS image: {e}")
            return False

    def _set_files(self, files: List[str]) -> bool:
        try:
            if not files:
                return False

            if len(files) == 1:
                path = files[0].replace('"', '\\"')
                subprocess.run(
                    ['osascript', '-e',
                     f'set theClip to POSIX file "{path}"\n'
                     f'set the clipboard to theClip'],
                    capture_output=True, timeout=5
                )
            else:
                alias_list = ", ".join([f'POSIX file "{f.replace(chr(34), chr(92)+chr(34))}"' for f in files])
                subprocess.run(
                    ['osascript', '-e',
                     f'set theFiles to {{{alias_list}}}\n'
                     f'set the clipboard to theFiles'],
                    capture_output=True, timeout=5
                )
            return True
        except Exception as e:
            print(f"Error setting macOS files: {e}")
            return False


class ClipboardMonitor:
    def __init__(self, on_change: Callable[[ClipboardData], None], interval: int = 500):
        self.on_change = on_change
        self.interval = interval / 1000.0
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._last_content: str = ""
        self._last_change_count: int = 0

        if is_windows():
            self._backend = WindowsClipboardBackend()
        elif is_macos():
            self._backend = MacOSClipboardBackend()
        else:
            self._backend = MacOSClipboardBackend()

    def _get_change_count(self) -> int:
        if is_macos():
            try:
                result = subprocess.run(
                    ['osascript', '-e',
                     'return (clipboard info) as text'],
                    capture_output=True, text=True, timeout=2
                )
                return hash(result.stdout)
            except Exception:
                return 0
        else:
            try:
                import ctypes
                return ctypes.windll.user32.GetClipboardSequenceNumber()
            except Exception:
                return 0

    def _content_to_string(self, content: ClipboardData) -> str:
        if content.content_type == "image":
            return f"__IMAGE__{len(content.image_data)}"
        elif content.content_type == "file":
            return "\n".join(content.files)
        else:
            return content.text

    def _monitor_loop(self):
        while self._running:
            try:
                current_count = self._get_change_count()
                if current_count != self._last_change_count:
                    self._last_change_count = current_count
                    content = self._backend.get_content()
                    if content:
                        content_str = self._content_to_string(content)
                        if content_str != self._last_content:
                            self._last_content = content_str
                            self.on_change(content)
            except Exception as e:
                print(f"Monitor error: {e}")

            time.sleep(self.interval)

    def start(self):
        if self._running:
            return

        self._running = True
        self._last_change_count = self._get_change_count()
        content = self._backend.get_content()
        self._last_content = self._content_to_string(content) if content else ""

        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=1.0)
            self._thread = None

    def set_clipboard(self, content):
        try:
            if isinstance(content, ClipboardData):
                self._backend.set_content(content)
                self._last_content = self._content_to_string(content)
            else:
                text = str(content)
                data = ClipboardData(content_type="text", text=text)
                if is_windows() and self._is_file_path(text):
                    files = self._get_file_paths(text)
                    if files:
                        data = ClipboardData(content_type="file", files=files, text=text)
                self._backend.set_content(data)
                self._last_content = text
        except Exception as e:
            print(f"Error setting clipboard: {e}")

    def _is_file_path(self, content: str) -> bool:
        if not content:
            return False
        lines = content.strip().split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if not os.path.exists(line):
                return False
        return len(lines) > 0

    def _get_file_paths(self, content: str) -> List[str]:
        lines = content.strip().split('\n')
        return [l.strip() for l in lines if l.strip() and os.path.exists(l.strip())]
