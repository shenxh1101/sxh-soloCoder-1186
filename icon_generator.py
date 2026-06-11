from dataclasses import dataclass, field
from typing import List, Tuple, Optional

@dataclass
class IconConfig:
    DEFAULT_SIZES = {
        'favicon': [(16, 16), (32, 32), (48, 48)],
        'apple-touch-icon': [(180, 180)],
        'android-chrome': [(192, 192), (512, 512)],
        'mstile': [(150, 150)],
    }
    
    DEFAULT_FILENAMES = {
        'favicon': 'favicon.ico',
        'apple-touch-icon': 'apple-touch-icon.png',
        'android-chrome-192': 'android-chrome-192x192.png',
        'android-chrome-512': 'android-chrome-512x512.png',
        'mstile': 'mstile-150x150.png',
    }

@dataclass
class ProcessingOptions:
    corner_radius: int = 0
    background_color: Optional[str] = None
    shadow: bool = False
    shadow_blur: int = 10
    shadow_offset: Tuple[int, int] = (0, 4)
    shadow_color: str = 'rgba(0, 0, 0, 0.3)'
    custom_sizes: List[Tuple[int, int]] = field(default_factory=list)
    custom_filenames: dict = field(default_factory=dict)
    app_name: str = 'My App'
    app_short_name: str = 'App'
    theme_color: str = '#ffffff'
    background_color_manifest: str = '#ffffff'
