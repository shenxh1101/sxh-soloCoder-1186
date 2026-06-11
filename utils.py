import os
import hashlib
import zipfile
import io
from typing import List, Tuple, Optional
from werkzeug.utils import secure_filename
from PIL import Image

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'zip'}
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp'}

def allowed_file(filename: str, allowed: set = None) -> bool:
    if allowed is None:
        allowed = ALLOWED_EXTENSIONS
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed

def get_file_hash(file_content: bytes) -> str:
    return hashlib.sha256(file_content).hexdigest()

def get_image_hash(image: Image.Image) -> str:
    img_bytes = io.BytesIO()
    image.save(img_bytes, format='PNG')
    return hashlib.sha256(img_bytes.getvalue()).hexdigest()

def parse_color(color_str: Optional[str]) -> Optional[Tuple[int, int, int, int]]:
    if not color_str:
        return None
    color_str = color_str.strip()
    if color_str.startswith('#'):
        color_str = color_str[1:]
        if len(color_str) == 3:
            color_str = ''.join(c * 2 for c in color_str)
        if len(color_str) == 6:
            r = int(color_str[0:2], 16)
            g = int(color_str[2:4], 16)
            b = int(color_str[4:6], 16)
            return (r, g, b, 255)
        elif len(color_str) == 8:
            r = int(color_str[0:2], 16)
            g = int(color_str[2:4], 16)
            b = int(color_str[4:6], 16)
            a = int(color_str[6:8], 16)
            return (r, g, b, a)
    return None

def parse_rgba(color_str: Optional[str]) -> Optional[Tuple[int, int, int, int]]:
    if not color_str:
        return None
    color_str = color_str.strip()
    if color_str.startswith('rgba'):
        try:
            parts = color_str[5:-1].split(',')
            r = int(parts[0].strip())
            g = int(parts[1].strip())
            b = int(parts[2].strip())
            a = int(float(parts[3].strip()) * 255)
            return (r, g, b, a)
        except:
            pass
    return parse_color(color_str)

def parse_size_str(size_str: str) -> Optional[Tuple[int, int]]:
    try:
        size_str = size_str.strip()
        if 'x' in size_str.lower():
            w, h = size_str.lower().split('x', 1)
            return (int(w.strip()), int(h.strip()))
        size = int(size_str)
        return (size, size)
    except:
        return None

def save_uploaded_file(file_storage, upload_folder: str) -> str:
    filename = secure_filename(file_storage.filename)
    filepath = os.path.join(upload_folder, filename)
    counter = 1
    while os.path.exists(filepath):
        name, ext = os.path.splitext(filename)
        filepath = os.path.join(upload_folder, f"{name}_{counter}{ext}")
        counter += 1
    file_storage.save(filepath)
    return filepath

def extract_zip(zip_path: str, extract_folder: str) -> List[str]:
    image_paths = []
    with zipfile.ZipFile(zip_path, 'r') as zf:
        for member in zf.namelist():
            if member.startswith('__MACOSX') or member.startswith('.'):
                continue
            if '/' in member and not member.endswith('/'):
                filename = member.rsplit('/', 1)[-1]
            else:
                filename = member
            if filename.endswith('/'):
                continue
            if allowed_file(filename, ALLOWED_IMAGE_EXTENSIONS):
                content = zf.read(member)
                safe_name = secure_filename(filename)
                output_path = os.path.join(extract_folder, safe_name)
                counter = 1
                while os.path.exists(output_path):
                    name, ext = os.path.splitext(safe_name)
                    output_path = os.path.join(extract_folder, f"{name}_{counter}{ext}")
                    counter += 1
                with open(output_path, 'wb') as f:
                    f.write(content)
                image_paths.append(output_path)
    return image_paths

def load_image(filepath: str) -> Image.Image:
    img = Image.open(filepath)
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    return img

def ensure_fit(image: Image.Image, target_size: Tuple[int, int]) -> Image.Image:
    src_w, src_h = image.size
    dst_w, dst_h = target_size
    ratio = max(dst_w / src_w, dst_h / src_h)
    new_w = int(src_w * ratio)
    new_h = int(src_h * ratio)
    img = image.resize((new_w, new_h), Image.LANCZOS)
    left = (new_w - dst_w) // 2
    top = (new_h - dst_h) // 2
    right = left + dst_w
    bottom = top + dst_h
    return img.crop((left, top, right, bottom))

def hex_color(color_tuple: Tuple[int, int, int, int]) -> str:
    return f'#{color_tuple[0]:02x}{color_tuple[1]:02x}{color_tuple[2]:02x}'
