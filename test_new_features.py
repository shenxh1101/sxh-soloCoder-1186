import requests
import json
import time

BASE_URL = 'http://127.0.0.1:5000'
TEST_IMAGE = 'test_images/test_icon.png'

def test_full_flow():
    print('=' * 60)
    print('测试1: 完整流程 - 跳过裁剪直接生成')
    print('=' * 60)
    
    upload_url = f'{BASE_URL}/upload'
    files = {'files': open(TEST_IMAGE, 'rb')}
    data = {
        'corner_radius': '30',
        'shadow': 'true',
        'shadow_blur': '15',
        'shadow_offset_x': '0',
        'shadow_offset_y': '5',
        'shadow_color': 'rgba(0, 0, 0, 0.3)',
        'app_name': '我的测试应用',
        'app_short_name': '测试',
        'theme_color': '#ff6b6b',
        'skip_crop': 'true',
        'filename_apple-touch-icon-180x180': 'my-icon.png',
    }
    
    print('上传图片...')
    response = requests.post(upload_url, files=files, data=data)
    print(f'上传状态: {response.status_code}')
    result = response.json()
    print(f'成功: {result.get("success")}')
    print(f'skip_crop: {result.get("skip_crop")}')
    
    if not result.get('success'):
        print(f'错误: {result.get("error")}')
        return False
    
    upload_id = result.get('upload_id')
    print(f'upload_id: {upload_id}')
    
    print('\n生成图标...')
    generate_url = f'{BASE_URL}/generate'
    gen_data = {
        'upload_id': upload_id,
        'corner_radius': '30',
        'shadow': 'true',
        'shadow_blur': '15',
        'app_name': '我的测试应用',
        'app_short_name': '测试',
        'theme_color': '#ff6b6b',
    }
    gen_response = requests.post(generate_url, data=gen_data)
    print(f'生成状态: {gen_response.status_code}')
    gen_result = gen_response.json()
    print(f'成功: {gen_result.get("success")}')
    
    if not gen_result.get('success'):
        print(f'错误: {gen_result.get("error")}')
        return False
    
    batch_id = gen_result.get('batch_id')
    print(f'batch_id: {batch_id}')
    
    for r in gen_result['results']:
        print(f'\n文件列表:')
        for k, v in r.get('files', {}).items():
            print(f'  {k}: {v.get("filename")} ({v.get("type")})')
    
    print('\n' + '=' * 60)
    print('测试2: 验证配置文件内容')
    print('=' * 60)
    
    first_result = gen_result['results'][0]
    files = first_result['files']
    
    preview_file_url = f'{BASE_URL}/preview/file/{batch_id}/{first_result["original_name"]}'
    
    manifest_url = f'{preview_file_url}/manifest.json'
    manifest_resp = requests.get(manifest_url)
    if manifest_resp.status_code == 200:
        manifest_data = manifest_resp.json()
        print(f'manifest.json:')
        print(f'  name: {manifest_data.get("name")}')
        print(f'  short_name: {manifest_data.get("short_name")}')
        print(f'  theme_color: {manifest_data.get("theme_color")}')
        print(f'  icons数量: {len(manifest_data.get("icons", []))}')
        
        assert manifest_data.get('name') == '我的测试应用', '应用名称不匹配'
        assert manifest_data.get('short_name') == '测试', '短名称不匹配'
        assert manifest_data.get('theme_color') == '#ff6b6b', '主题色不匹配'
        print('  ✓ manifest.json 内容正确')
    else:
        print(f'  ✗ 无法获取 manifest.json: {manifest_resp.status_code}')
    
    browserconfig_url = f'{preview_file_url}/browserconfig.xml'
    bc_resp = requests.get(browserconfig_url)
    if bc_resp.status_code == 200:
        bc_content = bc_resp.text
        print(f'\nbrowserconfig.xml:')
        print(f'  包含主题色 #ff6b6b: {"#ff6b6b" in bc_content}')
        assert '#ff6b6b' in bc_content, 'browserconfig 主题色不匹配'
        print('  ✓ browserconfig.xml 内容正确')
    
    print('\n' + '=' * 60)
    print('测试3: 验证自定义文件名')
    print('=' * 60)
    
    apple_icon = files.get('apple-touch-icon-180x180')
    if apple_icon:
        print(f'Apple Touch 图标文件名: {apple_icon["filename"]}')
        assert apple_icon['filename'] == 'my-icon.png', '自定义文件名不匹配'
        print('  ✓ 自定义文件名生效')
    
    print('\n' + '=' * 60)
    print('测试4: 历史记录')
    print('=' * 60)
    
    history_url = f'{BASE_URL}/history'
    history_resp = requests.get(history_url)
    print(f'历史记录页面状态: {history_resp.status_code}')
    assert history_resp.status_code == 200, '历史记录页面无法访问'
    print('  ✓ 历史记录页面可访问')
    
    stats_url = f'{BASE_URL}/api/cache/stats'
    stats_resp = requests.get(stats_url)
    stats = stats_resp.json()
    print(f'缓存统计: {stats}')
    print(f'历史记录数: {stats.get("history_count")}')
    assert stats.get('history_count', 0) >= 1, '历史记录数应该>=1'
    print('  ✓ 历史记录功能正常')
    
    print('\n' + '=' * 60)
    print('测试5: 预览页面')
    print('=' * 60)
    
    preview_url = f'{BASE_URL}/preview/{batch_id}'
    preview_resp = requests.get(preview_url)
    print(f'预览页面状态: {preview_resp.status_code}')
    assert preview_resp.status_code == 200, '预览页面无法访问'
    print('  ✓ 预览页面可访问')
    
    print('\n' + '=' * 60)
    print('✅ 所有测试通过!')
    print('=' * 60)
    return True

if __name__ == '__main__':
    try:
        success = test_full_flow()
        exit(0 if success else 1)
    except Exception as e:
        print(f'\n❌ 测试失败: {e}')
        import traceback
        traceback.print_exc()
        exit(1)
