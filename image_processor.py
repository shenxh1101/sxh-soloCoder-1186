import io
import math
from typing import Tuple, Optional
from PIL import Image, ImageDraw, ImageFilter
from utils import parse_color, parse_rgba, ensure_fit
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
    img = ensure_fit(image, size)
    return process_image(img, options)

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
