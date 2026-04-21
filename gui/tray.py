import pystray
from PIL import Image, ImageDraw
from typing import Callable, Optional
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class SystemTray:
    def __init__(self, on_show: Callable[[], None], on_exit: Callable[[], None]):
        self.on_show = on_show
        self.on_exit = on_exit
        self._icon: Optional[pystray.Icon] = None
    
    def _create_icon_image(self) -> Image.Image:
        size = 64
        image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        
        draw.rounded_rectangle(
            [8, 8, size - 8, size - 8],
            radius=12,
            fill=(0, 113, 227, 255)
        )
        
        draw.rectangle([18, 20, size - 18, 28], fill=(255, 255, 255, 255))
        draw.rectangle([18, 30, size - 18, 38], fill=(255, 255, 255, 255))
        draw.rectangle([18, 40, size - 28, 48], fill=(255, 255, 255, 255))
        
        return image
    
    def _create_menu(self) -> pystray.Menu:
        return pystray.Menu(
            pystray.MenuItem("显示窗口", self._on_show, default=True),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("退出", self._on_exit)
        )
    
    def _on_show(self, icon=None, item=None):
        self.on_show()
    
    def _on_exit(self, icon=None, item=None):
        self.on_exit()
    
    def create(self):
        image = self._create_icon_image()
        menu = self._create_menu()
        
        self._icon = pystray.Icon(
            "clipboard_manager",
            image,
            "剪切板管理器",
            menu
        )
    
    def run(self):
        if self._icon:
            self._icon.run_detached()
    
    def stop(self):
        if self._icon:
            self._icon.stop()
