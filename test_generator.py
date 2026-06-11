import os
from icon_service import generate_icon_set
from icon_generator import ProcessingOptions

options = ProcessingOptions(
    corner_radius=50,
    background_color=None,
    shadow=True,
    shadow_blur=10,
    shadow_offset=(0, 4),
    shadow_color='rgba(0, 0, 0, 0.3)',
    app_name='Test App',
    app_short_name='Test',
    theme_color='#667eea',
    background_color_manifest='#ffffff'
)

output_dir = 'test_output'
os.makedirs(output_dir, exist_ok=True)

result = generate_icon_set('test_images/test_icon.png', options, output_dir)

print('Generated files:')
for key, info in result.items():
    print(f'  {key}: {info["filename"]}')
    if info.get('size'):
        print(f'    Size: {info["size"]}')
    elif info.get('sizes'):
        print(f'    Sizes: {info["sizes"]}')

print('\nAll files generated successfully!')
print('\nGenerated files in test_output/:')
for f in os.listdir(output_dir):
    fpath = os.path.join(output_dir, f)
    size = os.path.getsize(fpath)
    print(f'  {f} ({size} bytes)')
