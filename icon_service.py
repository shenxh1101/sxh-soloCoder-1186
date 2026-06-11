import os
import json
from typing import Dict, List, Tuple, Optional
from PIL import Image
from icon_generator import IconConfig, ProcessingOptions
from image_processor import generate_single_icon, generate_favicon, generate_png, image_to_bytes
from utils import load_image, hex_color

class IconService:
    def __init__(self, output_folder: str):
        self.output_folder = output_folder
        os.makedirs(self.output_folder, exist_ok=True)
    
    def get_all_sizes(self, options: ProcessingOptions) -> Dict[str, List[Tuple[int, int]]]:
        sizes = {}
        sizes['favicon'] = IconConfig.DEFAULT_SIZES['favicon'].copy()
        sizes['apple-touch-icon'] = IconConfig.DEFAULT_SIZES['apple-touch-icon'].copy()
        sizes['android-chrome'] = IconConfig.DEFAULT_SIZES['android-chrome'].copy()
        sizes['mstile'] = IconConfig.DEFAULT_SIZES['mstile'].copy()
        
        if options.custom_sizes:
            sizes['custom'] = options.custom_sizes
        
        return sizes
    
    def get_filename(self, icon_type: str, size: Tuple[int, int], 
                     options: ProcessingOptions, index: int = 0) -> str:
        filenames = options.custom_filenames if options.custom_filenames else {}
        
        key = f'{icon_type}-{size[0]}x{size[1]}'
        if key in filenames:
            return filenames[key]
        
        if icon_type == 'favicon':
            return filenames.get('favicon', IconConfig.DEFAULT_FILENAMES['favicon'])
        elif icon_type == 'apple-touch-icon':
            return filenames.get('apple-touch-icon', IconConfig.DEFAULT_FILENAMES['apple-touch-icon'])
        elif icon_type == 'android-chrome':
            if size[0] == 192:
                return filenames.get('android-chrome-192', IconConfig.DEFAULT_FILENAMES['android-chrome-192'])
            elif size[0] == 512:
                return filenames.get('android-chrome-512', IconConfig.DEFAULT_FILENAMES['android-chrome-512'])
        elif icon_type == 'mstile':
            return filenames.get('mstile', IconConfig.DEFAULT_FILENAMES['mstile'])
        elif icon_type == 'custom':
            return filenames.get(key, f'custom-{size[0]}x{size[1]}.png')
        
        return f'{icon_type}-{size[0]}x{size[1]}.png'
    
    def generate_icons(self, image: Image.Image, options: ProcessingOptions,
                       output_dir: str) -> Dict:
        os.makedirs(output_dir, exist_ok=True)
        
        all_sizes = self.get_all_sizes(options)
        generated_files = {}
        generated_images = {}
        
        for icon_type, size_list in all_sizes.items():
            for idx, size in enumerate(size_list):
                filename = self.get_filename(icon_type, size, options, idx)
                filepath = os.path.join(output_dir, filename)
                
                icon_img = generate_single_icon(image, size, options)
                generated_images[(icon_type, size)] = icon_img
                
                if icon_type == 'favicon':
                    continue
                else:
                    generate_png(icon_img, filepath)
                    generated_files[f'{icon_type}-{size[0]}x{size[1]}'] = {
                        'path': filepath,
                        'filename': filename,
                        'size': size,
                        'type': icon_type
                    }
        
        favicon_sizes = all_sizes['favicon']
        favicon_images = [(generated_images[('favicon', s)], s) for s in favicon_sizes]
        favicon_filename = self.get_filename('favicon', (0, 0), options)
        favicon_path = os.path.join(output_dir, favicon_filename)
        generate_favicon(favicon_images, favicon_path)
        generated_files['favicon'] = {
            'path': favicon_path,
            'filename': favicon_filename,
            'sizes': favicon_sizes,
            'type': 'favicon'
        }
        
        manifest_content = self.generate_manifest(options, generated_files)
        manifest_path = os.path.join(output_dir, 'manifest.json')
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest_content, f, indent=2, ensure_ascii=False)
        generated_files['manifest'] = {
            'path': manifest_path,
            'filename': 'manifest.json',
            'type': 'manifest'
        }
        
        browserconfig_content = self.generate_browserconfig(options, generated_files)
        browserconfig_path = os.path.join(output_dir, 'browserconfig.xml')
        with open(browserconfig_path, 'w', encoding='utf-8') as f:
            f.write(browserconfig_content)
        generated_files['browserconfig'] = {
            'path': browserconfig_path,
            'filename': 'browserconfig.xml',
            'type': 'browserconfig'
        }
        
        html_snippet = self.generate_html_snippet(options, generated_files)
        html_path = os.path.join(output_dir, 'icons.html')
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_snippet)
        generated_files['html'] = {
            'path': html_path,
            'filename': 'icons.html',
            'type': 'html',
            'content': html_snippet
        }
        
        return generated_files
    
    def generate_manifest(self, options: ProcessingOptions, 
                          generated_files: Dict) -> Dict:
        icons = []
        
        for key, info in generated_files.items():
            if info['type'] == 'android-chrome':
                icons.append({
                    'src': info['filename'],
                    'sizes': f"{info['size'][0]}x{info['size'][1]}",
                    'type': 'image/png',
                    'purpose': 'any maskable'
                })
        
        theme_color = options.theme_color
        bg_color = options.background_color_manifest
        
        return {
            'name': options.app_name,
            'short_name': options.app_short_name,
            'icons': icons,
            'theme_color': theme_color,
            'background_color': bg_color,
            'display': 'standalone'
        }
    
    def generate_browserconfig(self, options: ProcessingOptions,
                                generated_files: Dict) -> str:
        mstile_info = None
        for key, info in generated_files.items():
            if info['type'] == 'mstile':
                mstile_info = info
                break
        
        tile_color = options.theme_color
        if not tile_color.startswith('#'):
            tile_color = '#ffffff'
        
        mstile_filename = mstile_info['filename'] if mstile_info else 'mstile-150x150.png'
        
        return f'''<?xml version="1.0" encoding="utf-8"?>
<browserconfig>
    <msapplication>
        <tile>
            <square150x150logo src="{mstile_filename}"/>
            <TileColor>{tile_color}</TileColor>
        </tile>
    </msapplication>
</browserconfig>'''
    
    def generate_html_snippet(self, options: ProcessingOptions,
                               generated_files: Dict) -> str:
        lines = []
        lines.append('<!-- Icons -->')
        
        if 'favicon' in generated_files:
            favicon_name = generated_files['favicon']['filename']
            lines.append(f'<link rel="icon" type="image/x-icon" href="{favicon_name}">')
            lines.append(f'<link rel="shortcut icon" type="image/x-icon" href="{favicon_name}">')
        
        for key, info in generated_files.items():
            if info['type'] == 'apple-touch-icon':
                size = info['size']
                lines.append(f'<link rel="apple-touch-icon" sizes="{size[0]}x{size[1]}" href="{info["filename"]}">')
        
        for key, info in generated_files.items():
            if info['type'] == 'android-chrome':
                size = info['size']
                lines.append(f'<link rel="icon" type="image/png" sizes="{size[0]}x{size[1]}" href="{info["filename"]}">')
        
        lines.append(f'<meta name="theme-color" content="{options.theme_color}">')
        lines.append(f'<link rel="manifest" href="manifest.json">')
        lines.append(f'<meta name="msapplication-config" content="browserconfig.xml">')
        lines.append(f'<meta name="msapplication-TileColor" content="{options.theme_color}">')
        
        if 'mstile' in generated_files:
            mstile_name = generated_files['mstile']['filename']
            lines.append(f'<meta name="msapplication-TileImage" content="{mstile_name}">')
        
        html_content = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Generated Icons</title>
{chr(10).join(f'    {line}' for line in lines)}
</head>
<body>
    <h1>Icon Preview</h1>
    <div class="icons-preview">
{chr(10).join(f'        <div><img src="{info["filename"]}" alt="{key}"><p>{info["filename"]}</p></div>' for key, info in generated_files.items() if info['type'] not in ['manifest', 'browserconfig', 'html'])}
    </div>
    <h2>HTML Code Snippet</h2>
    <pre><code>{chr(10).join(lines)}</code></pre>
</body>
</html>'''
        
        return html_content

def generate_icon_set(image_path: str, options: ProcessingOptions, 
                      output_dir: str) -> Dict:
    service = IconService(output_dir)
    image = load_image(image_path)
    return service.generate_icons(image, options, output_dir)
