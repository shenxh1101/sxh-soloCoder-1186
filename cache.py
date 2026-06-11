import os
import json
import pickle
import hashlib
import shutil
from typing import Optional, Dict, Any, Tuple
from icon_generator import ProcessingOptions

class CacheManager:
    def __init__(self, cache_folder: str):
        self.cache_folder = cache_folder
        self.index_file = os.path.join(cache_folder, 'cache_index.json')
        os.makedirs(self.cache_folder, exist_ok=True)
        self._load_index()
    
    def _load_index(self):
        if os.path.exists(self.index_file):
            try:
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    self.index = json.load(f)
            except:
                self.index = {}
        else:
            self.index = {}
    
    def _save_index(self):
        with open(self.index_file, 'w', encoding='utf-8') as f:
            json.dump(self.index, f, indent=2)
    
    def _get_options_hash(self, options: ProcessingOptions) -> str:
        options_dict = {
            'corner_radius': options.corner_radius,
            'background_color': options.background_color,
            'shadow': options.shadow,
            'shadow_blur': options.shadow_blur,
            'shadow_offset': list(options.shadow_offset),
            'shadow_color': options.shadow_color,
            'custom_sizes': [list(s) for s in options.custom_sizes],
            'custom_filenames': options.custom_filenames,
            'app_name': options.app_name,
            'app_short_name': options.app_short_name,
            'theme_color': options.theme_color,
            'background_color_manifest': options.background_color_manifest,
            'crop': {
                'enabled': options.crop.enabled,
                'x': options.crop.x,
                'y': options.crop.y,
                'width': options.crop.width,
                'height': options.crop.height,
                'scale': options.crop.scale,
                'mode': options.crop.mode
            } if options.crop else None
        }
        options_str = json.dumps(options_dict, sort_keys=True)
        return hashlib.md5(options_str.encode('utf-8')).hexdigest()
    
    def get_cache_key(self, file_hash: str, options: ProcessingOptions) -> str:
        options_hash = self._get_options_hash(options)
        return f"{file_hash}_{options_hash}"
    
    def get(self, cache_key: str) -> Optional[Dict[str, Any]]:
        if cache_key not in self.index:
            return None
        
        cache_entry = self.index[cache_key]
        cache_dir = os.path.join(self.cache_folder, cache_key)
        
        if not os.path.exists(cache_dir):
            del self.index[cache_key]
            self._save_index()
            return None
        
        return {
            'files': cache_entry.get('files', {}),
            'cache_dir': cache_dir,
            'original_name': cache_entry.get('original_name', '')
        }
    
    def set(self, cache_key: str, generated_files: Dict[str, Any], 
            source_dir: str, original_name: str = '') -> str:
        cache_dir = os.path.join(self.cache_folder, cache_key)
        
        if os.path.exists(cache_dir):
            shutil.rmtree(cache_dir)
        
        shutil.copytree(source_dir, cache_dir)
        
        files_info = {}
        for key, info in generated_files.items():
            if isinstance(info, dict) and 'filename' in info:
                files_info[key] = {
                    'filename': info['filename'],
                    'type': info.get('type', ''),
                    'size': info.get('size'),
                    'sizes': info.get('sizes')
                }
        
        self.index[cache_key] = {
            'files': files_info,
            'original_name': original_name
        }
        self._save_index()
        
        return cache_dir
    
    def clear(self):
        for item in os.listdir(self.cache_folder):
            item_path = os.path.join(self.cache_folder, item)
            if os.path.isdir(item_path):
                shutil.rmtree(item_path)
            elif item != 'cache_index.json':
                os.remove(item_path)
        self.index = {}
        self._save_index()
    
    def get_stats(self) -> Dict[str, Any]:
        total_size = 0
        total_files = 0
        for cache_key in self.index:
            cache_dir = os.path.join(self.cache_folder, cache_key)
            if os.path.exists(cache_dir):
                for root, dirs, files in os.walk(cache_dir):
                    for f in files:
                        fp = os.path.join(root, f)
                        total_size += os.path.getsize(fp)
                        total_files += 1
        
        return {
            'cache_entries': len(self.index),
            'total_files': total_files,
            'total_size_mb': round(total_size / (1024 * 1024), 2)
        }
