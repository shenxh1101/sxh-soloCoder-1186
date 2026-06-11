import requests
from bs4 import BeautifulSoup
import re

BASE_URL = 'http://127.0.0.1:5000'
TEST_IMAGE = 'test_images/test_icon.png'

def test_preview_content():
    print('=' * 60)
    print('测试: 预览页面内容验证')
    print('=' * 60)
    
    upload_url = f'{BASE_URL}/upload'
    files = {'files': open(TEST_IMAGE, 'rb')}
    data = {
        'app_name': '预览测试应用',
        'app_short_name': '预览',
        'theme_color': '#4ecdc4',
        'skip_crop': 'true',
        'filename_favicon': 'my-favicon.ico',
        'filename_android-chrome-192x192': 'android-192.png',
    }
    
    print('上传并生成...')
    response = requests.post(upload_url, files=files, data=data)
    result = response.json()
    upload_id = result.get('upload_id')
    
    generate_url = f'{BASE_URL}/generate'
    gen_data = {'upload_id': upload_id}
    gen_resp = requests.post(generate_url, data=gen_data)
    gen_result = gen_resp.json()
    batch_id = gen_result.get('batch_id')
    
    print(f'batch_id: {batch_id}')
    
    print('\n获取预览页面...')
    preview_url = f'{BASE_URL}/preview/{batch_id}'
    preview_resp = requests.get(preview_url)
    print(f'预览页面状态: {preview_resp.status_code}')
    
    html_content = preview_resp.text
    
    print('\n' + '=' * 60)
    print('验证1: HTML代码片段中的主题色')
    print('=' * 60)
    
    theme_color_matches = re.findall(r'name="theme-color" content="([^"]+)"', html_content)
    print(f'找到 theme-color 标签: {len(theme_color_matches)} 个')
    for i, color in enumerate(theme_color_matches):
        print(f'  第{i+1}个: {color}')
        if color == '#4ecdc4':
            print('    ✓ 正确')
        else:
            print('    ✗ 错误，应该是 #4ecdc4')
    
    tile_color_matches = re.findall(r'msapplication-TileColor" content="([^"]+)"', html_content)
    print(f'\n找到 msapplication-TileColor 标签: {len(tile_color_matches)} 个')
    for i, color in enumerate(tile_color_matches):
        print(f'  第{i+1}个: {color}')
        if color == '#4ecdc4':
            print('    ✓ 正确')
        else:
            print('    ✗ 错误，应该是 #4ecdc4')
    
    print('\n' + '=' * 60)
    print('验证2: 自定义文件名是否在HTML代码片段中')
    print('=' * 60)
    
    if 'my-favicon.ico' in html_content:
        print('✓ favicon 自定义文件名 (my-favicon.ico) 出现在页面中')
    else:
        print('✗ favicon 自定义文件名未找到')
    
    if 'android-192.png' in html_content:
        print('✓ android-chrome 自定义文件名 (android-192.png) 出现在页面中')
    else:
        print('✗ android-chrome 自定义文件名未找到')
    
    print('\n' + '=' * 60)
    print('验证3: 预览页面中的options变量')
    print('=' * 60)
    
    options_match = re.search(r'var options = (\{[^;]+\});', html_content)
    if options_match:
        options_str = options_match.group(1)
        print(f'找到 options 变量')
        if '预览测试应用' in options_str:
            print('✓ options 包含正确的应用名称')
        else:
            print('✗ options 不包含正确的应用名称')
        if '#4ecdc4' in options_str:
            print('✓ options 包含正确的主题色')
        else:
            print('✗ options 不包含正确的主题色')
    else:
        print('✗ 未找到 options 变量')
    
    print('\n' + '=' * 60)
    print('验证4: 实际文件内容验证 (manifest.json)')
    print('=' * 60)
    
    first_result = gen_result['results'][0]
    preview_file_url = f'{BASE_URL}/preview/file/{batch_id}/{first_result["original_name"]}'
    
    manifest_url = f'{preview_file_url}/manifest.json'
    manifest_resp = requests.get(manifest_url)
    manifest_data = manifest_resp.json()
    
    print(f'应用名称: {manifest_data.get("name")}')
    print(f'短名称: {manifest_data.get("short_name")}')
    print(f'主题色: {manifest_data.get("theme_color")}')
    
    print(f'\n验证文件名是否匹配自定义:')
    for icon in manifest_data.get('icons', []):
        print(f'  - {icon["src"]} ({icon["sizes"]})')
    
    print('\n' + '=' * 60)
    print('验证5: 下载ZIP文件')
    print('=' * 60)
    
    download_url = f'{BASE_URL}/download/{batch_id}'
    download_resp = requests.get(download_url)
    print(f'下载状态: {download_resp.status_code}')
    print(f'文件大小: {len(download_resp.content)} bytes')
    print(f'Content-Type: {download_resp.headers.get("Content-Type")}')
    
    if download_resp.headers.get('Content-Type') == 'application/zip':
        print('✓ ZIP下载正常')
    
    print('\n' + '=' * 60)
    print('✅ 预览内容验证完成!')
    print('=' * 60)

if __name__ == '__main__':
    try:
        test_preview_content()
    except Exception as e:
        print(f'\n❌ 测试失败: {e}')
        import traceback
        traceback.print_exc()
