import io
import math
from typing import Tuple, Optional
from PIL import Image, ImageDraw, ImageFilter
from utils import parse_color, parse_rgba
from icon_generator import ProcessingOptions

def apply_background(image: Image.Image, bg_color: Optional[str]) -> Image.Image:
    if not bg_color:
        return image
    color = parse_color(bg_color)
    if not color:
        return image
    width, height = image.size
    bg = Image.new('RGBA', (width, height), color)
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    bg.paste(image, (0, 0), image)
    return bg

def apply_corner_radius(image: Image.Image, radius: int) -> Image.Image:
    if radius <= 0:
        return image
    width, height = image.size
    radius = min(radius, width // 2, height // 2)
    mask = Image.new('L', (width, height), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, width, height), radius=radius, fill=255)
    result = image.copy()
    result.putalpha(mask)
    return result

def apply_shadow(image: Image.Image, blur: int = 10, 
                 offset: Tuple[int, int] = (0, 4), 
                 shadow_color_str: str = 'rgba(0, 0, 0, 0.3)') -> Image.Image:
    shadow_color = parse_rgba(shadow_color_str)
    if not shadow_color:
        shadow_color = (0, 0, 0, 77)
    
    width, height = image.size
    offset_x, offset_y = offset
    total_width = width + abs(offset_x) + blur * 2
    total_height = height + abs(offset_y) + blur * 2
    
    shadow_layer = Image.new('RGBA', (total_width, total_height), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow_layer)
    
    shadow_position_x = blur + max(0, offset_x)
    shadow_position_y = blur + max(0, offset_y)
    
    alpha = image.split()[3] if image.mode == 'RGBA' else Image.new('L', image.size, 255)
    shadow_rgb = Image.new('RGB', image.size, shadow_color[:3])
    shadow_alpha = Image.new('L', image.size, shadow_color[3])
    shadow_alpha = Image.composite(shadow_alpha, Image.new('L', image.size, 0), alpha)
    shadow_img = Image.merge('RGBA', [*shadow_rgb.split(), shadow_alpha])
    
    shadow_layer.paste(shadow_img, (shadow_position_x, shadow_position_y), shadow_alpha)
    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(radius=blur / 2))
    
    result = Image.new('RGBA', (total_width, total_height), (0, 0, 0, 0))
    result.paste(shadow_layer, (0, 0), shadow_layer)
    
    image_position_x = blur - min(0, offset_x)
    image_position_y = blur - min(0, offset_y)
    result.paste(image, (image_position_x, image_position_y), image)
    
    return result

def process_image(image: Image.Image, options: ProcessingOptions) -> Image.Image:
    img = image.copy()
    
    if options.background_color:
        img = apply_background(img, options.background_color)
    
    if options.corner_radius > 0:
        img = apply_corner_radius(img, options.corner_radius)
    
    if options.shadow:
        img = apply_shadow(
            img,
            blur=options.shadow_blur,
            offset=options.shadow_offset,
            shadow_color_str=options.shadow_color
        )
    
    return img

def generate_single_icon(image: Image.Image, size: Tuple[int, int], 
                         options: ProcessingOptions) -> Image.Image:
    target_w, target_h = size
    
    effect_padding_x = 0
    effect_padding_y = 0
    
    if options.shadow:
        blur = options.shadow_blur
        offset_x, offset_y = options.shadow_offset
        effect_padding_x = blur + abs(offset_x)
        effect_padding_y = blur + abs(offset_y)
    
    content_w = target_w - effect_padding_x * 2
    content_h = target_h - effect_padding_y * 2
    
    if content_w < 1:
        content_w = 1
    if content_h < 1:
        content_h = 1
    
    content_img = ensure_fit_content(image, (content_w, content_h))
    
    processed = process_image(content_img, options)
    
    result = Image.new('RGBA', (target_w, target_h), (0, 0, 0, 0))
    
    proc_w, proc_h = processed.size
    
    paste_x = (target_w - proc_w) // 2
    paste_y = (target_h - proc_h) // 2
    
    if options.shadow:
        blur = options.shadow_blur
        offset_x, offset_y = options.shadow_offset
        
        paste_x = blur - min(0, offset_x)
        paste_y = blur - min(0, offset_y)
        
        content_center_x = target_w // 2
        content_center_y = target_h // 2
        
        content_left = content_center_x - content_w // 2
        content_top = content_center_y - content_h // 2
        
        paste_x = content_left - (blur - min(0, offset_x))
        paste_y = content_top - (blur - min(0, offset_y))
    
    if paste_x + proc_w > target_w:
        paste_x = target_w - proc_w
    if paste_y + proc_h > target_h:
        paste_y = target_h - proc_h
    if paste_x < 0:
        paste_x = 0
    if paste_y < 0:
        paste_y = 0
    
    result.paste(processed, (paste_x, paste_y), processed)
    
    return result

def ensure_fit_content(image: Image.Image, target_size: Tuple[int, int]) -> Image.Image:
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

def generate_favicon(images: list, output_path: str) -> None:
    if not images:
        raise ValueError("No images provided for favicon generation")
    
    sorted_images = sorted(images, key=lambda x: x[0].size[0], reverse=True)
    base_img = sorted_images[0][0]
    
    sizes = [img[0].size for img in sorted_images]
    base_img.save(output_path, format='ICO', sizes=sizes)

def generate_png(image: Image.Image, output_path: str) -> None:
    image.save(output_path, format='PNG')

def image_to_bytes(image: Image.Image, format: str = 'PNG') -> bytes:
    buf = io.BytesIO()
    image.save(buf, format=format)
    return buf.getvalue()

def crop_image(image: Image.Image, x: int, y: int, width: int, height: int, 
               scale: float = 1.0, mode: str = 'cover', 
               target_size: Tuple[int, int] = None) -> Image.Image:
    img = image.copy()
    
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    
    if scale != 1.0 and scale > 0:
        new_w = int(img.size[0] * scale)
        new_h = int(img.size[1] * scale)
        img = img.resize((new_w, new_h), Image.LANCZOS)
    
    img_w, img_h = img.size
    
    if x < 0:
        x = 0
    if y < 0:
        y = 0
    if width <= 0 or x + width > img_w:
        width = img_w - x
    if height <= 0 or y + height > img_h:
        height = img_h - y
    
    cropped = img.crop((x, y, x + width, y + height))
    
    if target_size and mode == 'cover':
        return ensure_fit_content(cropped, target_size)
    elif target_size and mode == 'contain':
        tw, th = target_size
        cw, ch = cropped.size
        ratio = min(tw / cw, th / ch)
        new_w = int(cw * ratio)
        new_h = int(ch * ratio)
        resized = cropped.resize((new_w, new_h), Image.LANCZOS)
        result = Image.new('RGBA', target_size, (0, 0, 0, 0))
        px = (tw - new_w) // 2
        py = (th - new_h) // 2
        result.paste(resized, (px, py), resized)
        return result
    elif target_size and mode == 'fill':
        return cropped.resize(target_size, Image.LANCZOS)
    
    return cropped
