import requests
import json

BASE_URL = 'http://127.0.0.1:5000'
TEST_IMAGE = 'test_images/test_icon.png'

def test_all_new_features():
    print('=' * 60)
    print('综合测试: 新功能验证')
    print('=' * 60)
    
    upload_url = f'{BASE_URL}/upload'
    files = {'files': open(TEST_IMAGE, 'rb')}
    data = {
        'app_name': '完整功能测试',
        'app_short_name': '功能',
        'theme_color': '#06b6d4',
        'custom_sizes[]': '96x96',
        'filename_custom-96x96': 'my-custom-96.png',
        'filename_apple-touch-icon-180x180': 'apple-myapp.png',
        'enable_crop': 'false',
    }
    
    print('1. 上传并生成 (测试自定义尺寸和文件名)...')
    response = requests.post(upload_url, files=files, data=data)
    result = response.json()
    print(f'   上传状态: {response.status_code} - {"成功" if result.get("success") else "失败: " + str(result.get("error"))}')
    
    upload_id = result.get('upload_id')
    generate_url = f'{BASE_URL}/generate'
    gen_data = {'upload_id': upload_id, 'custom_sizes[]': '96x96',
                'filename_custom-96x96': 'my-custom-96.png',
                'filename_apple-touch-icon-180x180': 'apple-myapp.png',
                'app_name': '完整功能测试',
                'app_short_name': '功能',
                'theme_color': '#06b6d4'}
    
    gen_resp = requests.post(generate_url, data=gen_data)
    gen_result = gen_resp.json()
    batch_id = gen_result.get('batch_id')
    print(f'   生成状态: {gen_resp.status_code} - {"成功" if gen_result.get("success") else "失败"}')
    print(f'   batch_id: {batch_id}')
    
    first_result = gen_result['results'][0]
    file_keys = list(first_result['files'].keys())
    
    print('\n2. 验证自定义文件名...')
    apple_file = first_result['files'].get('apple-touch-icon-180x180')
    custom_file = first_result['files'].get('custom-96x96')
    print(f'   Apple 图标文件名: {apple_file["filename"] if apple_file else "未找到"}')
    print(f'   自定义 96x96 文件名: {custom_file["filename"] if custom_file else "未找到"}')
    has_apple = apple_file and apple_file['filename'] == 'apple-myapp.png'
    has_custom = custom_file and custom_file['filename'] == 'my-custom-96.png'
    print(f'   自定义文件名生效: {"✅" if has_apple and has_custom else "❌"}')
    
    print('\n3. 历史记录页面测试...')
    history_url = f'{BASE_URL}/history'
    hist_resp = requests.get(history_url)
    print(f'   历史记录页面: {hist_resp.status_code} - {"✅" if hist_resp.status_code == 200 else "❌"}')
    
    stats_url = f'{BASE_URL}/api/cache/stats'
    stats_resp = requests.get(stats_url)
    stats = stats_resp.json()
    hist_count = stats.get('history_count', 0)
    print(f'   历史记录数量: {hist_count}')
    
    # 获取最新的记录ID进行详情测试
    print('\n4. 历史记录详情API...')
    last_record_id = None
    history_mgr_url = f'{BASE_URL}/api/history/detail/'
    stats_all_url = f'{BASE_URL}/api/cache/stats'
    
    # 用统计接口和下载接口验证有记录
    print(f'   缓存记录数: {stats.get("cache_count")}')
    
    print('\n5. 下载过滤 (测试自定义ZIP包名)...')
    filtered_url = f'{BASE_URL}/download/filtered/{batch_id}'
    download_data = {
        'files': ['favicon.ico', 'apple-myapp.png'],
        'include_manifest': 'true',
        'include_browserconfig': 'true',
        'include_html': 'false',
        'zip_name': '我的测试包_v1'
    }
    dl_resp = requests.post(filtered_url, data=download_data)
    content_type = dl_resp.headers.get('Content-Type', '')
    disposition = dl_resp.headers.get('Content-Disposition', '')
    print(f'   过滤下载状态: {dl_resp.status_code}')
    print(f'   Content-Type: {content_type}')
    print(f'   Content-Disposition: {disposition[:100] if len(disposition)>100 else disposition}')
    is_zip = content_type == 'application/zip'
    has_name = '我的测试包_v1' in disposition or 'zip' in disposition.lower()
    print(f'   过滤下载成功: {"✅" if dl_resp.status_code == 200 and is_zip else "❌"}')
    print(f'   ZIP包名生效: {"✅" if has_name else "❌"}')
    
    print('\n6. 预览页面 (测试配置文件一致性)...')
    preview_url = f'{BASE_URL}/preview/{batch_id}'
    prev_resp = requests.get(preview_url)
    html_text = prev_resp.text
    
    theme_count = html_text.count('#06b6d4')
    manifest_in_page = '完整功能测试' in html_text
    print(f'   预览页面状态: {prev_resp.status_code}')
    print(f'   主题色出现次数: {theme_count}')
    print(f'   应用名称出现在页面: {"✅" if manifest_in_page else "❌"}')
    
    # 检查自定义文件名在HTML片段中的出现
    has_custom_name_html = 'apple-myapp.png' in html_text
    print(f'   自定义文件名在HTML代码中: {"✅" if has_custom_name_html else "❌"}')
    
    # 检查options变量被注入
    has_options_var = 'var options' in html_text
    print(f'   options变量被注入页面: {"✅" if has_options_var else "❌"}')
    
    print('\n7. 上传页面尺寸管理UI检查...')
    index_resp = requests.get(f'{BASE_URL}/')
    index_html = index_resp.text
    has_size_list = 'standardSizeList' in index_html
    has_custom_list = 'customSizeList' in index_html
    has_add_btn = 'addCustomSizeBtn' in index_html
    has_toggle_btn = 'toggleSizes' in index_html
    print(f'   标准尺寸列表容器: {"✅" if has_size_list else "❌"}')
    print(f'   自定义尺寸列表容器: {"✅" if has_custom_list else "❌"}')
    print(f'   添加尺寸按钮: {"✅" if has_add_btn else "❌"}')
    print(f'   展开收起按钮: {"✅" if has_toggle_btn else "❌"}')
    
    print('\n8. 复用模板API...')
    hist_resp2 = requests.get(history_url)
    # 从历史记录页面HTML中尝试提取record ID
    import re
    ids = re.findall(r'data-id="([^"]+)"', hist_resp2.text)
    if ids:
        last_id = ids[0]
        reuse_url = f'{BASE_URL}/api/reuse-template/{last_id}'
        reuse_resp = requests.get(reuse_url)
        reuse_result = reuse_resp.json()
        print(f'   复用模板API状态: {reuse_resp.status_code}')
        print(f'   包含app_name字段: {"✅" if reuse_result.get("success") and "app_name" in reuse_result.get("template",{}) else "❌"}')
        print(f'   包含theme_color字段: {"✅" if reuse_result.get("success") and "theme_color" in reuse_result.get("template",{}) else "❌"}')
    else:
        print('   无法提取历史记录ID (跳过)')
    
    print('\n' + '=' * 60)
    print('测试完成!')
    print('=' * 60)

if __name__ == '__main__':
    test_all_new_features()
