from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict, Any

@dataclass
class IconConfig:
    DEFAULT_SIZES: Dict[str, List[Tuple[int, int]]] = field(default_factory=lambda: {
        'favicon': [(16, 16), (32, 32), (48, 48)],
        'apple-touch-icon': [(180, 180)],
        'android-chrome': [(192, 192), (512, 512)],
        'mstile': [(150, 150)],
    })
    
    DEFAULT_FILENAMES: Dict[str, str] = field(default_factory=lambda: {
        'favicon': 'favicon.ico',
        'apple-touch-icon': 'apple-touch-icon.png',
        'android-chrome-192': 'android-chrome-192x192.png',
        'android-chrome-512': 'android-chrome-512x512.png',
        'mstile': 'mstile-150x150.png',
    })
    
    SIZE_LABELS: Dict[str, str] = field(default_factory=lambda: {
        'favicon': 'Favicon',
        'apple-touch-icon': 'Apple Touch Icon',
        'android-chrome-192': 'Android Chrome (192px)',
        'android-chrome-512': 'Android Chrome (512px)',
        'mstile': 'Windows 磁贴',
    })

@dataclass
class CropOptions:
    enabled: bool = False
    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0
    scale: float = 1.0
    mode: str = 'cover'

@dataclass
class ProcessingOptions:
    corner_radius: int = 0
    background_color: Optional[str] = None
    shadow: bool = False
    shadow_blur: int = 10
    shadow_offset: Tuple[int, int] = (0, 4)
    shadow_color: str = 'rgba(0, 0, 0, 0.3)'
    custom_sizes: List[Tuple[int, int]] = field(default_factory=list)
    custom_filenames: Dict[str, str] = field(default_factory=dict)
    app_name: str = 'My App'
    app_short_name: str = 'App'
    theme_color: str = '#ffffff'
    background_color_manifest: str = '#ffffff'
    crop: CropOptions = field(default_factory=CropOptions)

@dataclass
class HistoryRecord:
    id: str
    original_name: str
    file_hash: str
    cache_key: str
    options: Dict[str, Any]
    created_at: str
    cached: bool
    file_count: int
