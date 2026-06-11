import os
from PIL import Image
from icon_service import generate_icon_set
from icon_generator import ProcessingOptions

options = ProcessingOptions(
    corner_radius=20,
    background_color=None,
    shadow=True,
    shadow_blur=10,
    shadow_offset=(0, 4),
    shadow_color='rgba(0, 0, 0, 0.3)',
    app_name='Test App',
    app_short_name='Test',
    theme_color='#667eea'
)

output_dir = 'test_size_output'
if os.path.exists(output_dir):
    import shutil
    shutil.rmtree(output_dir)

result = generate_icon_set('test_images/test_icon.png', options, output_dir)

print('=== 尺寸验证 ===')
for key, info in result.items():
    if info.get('type') in ['manifest', 'browserconfig', 'html']:
        continue
    
    filepath = info['path']
    if os.path.exists(filepath) and filepath.lower().endswith('.png'):
        with Image.open(filepath) as img:
            expected = info.get('size')
            actual = img.size
            match = expected == actual
            print(f'{key}:')
            print(f'  文件: {info["filename"]}')
            print(f'  预期尺寸: {expected}')
            print(f'  实际尺寸: {actual}')
            print(f'  匹配: {"✓" if match else "✗"}')
            print()

print('=== favicon.ico 尺寸验证 ===')
favicon_path = result['favicon']['path']
with Image.open(favicon_path) as ico:
    print(f'favicon包含 {len(ico.info.get("sizes", [])) if ico.info.get("sizes") else "多个"} 尺寸')
    try:
        for i in range(5):
            try:
                ico.seek(i)
                print(f'  尺寸 {i+1}: {ico.size}')
            except EOFError:
                break
    except:
        pass

print('\n✓ 尺寸验证完成')
