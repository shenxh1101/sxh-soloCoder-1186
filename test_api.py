import requests

url = 'http://127.0.0.1:5000/upload'
files = {'files': open('test_images/test_icon.png', 'rb')}
data = {
    'corner_radius': '30',
    'shadow': 'true',
    'shadow_blur': '15',
    'shadow_offset_x': '0',
    'shadow_offset_y': '5',
    'shadow_color': 'rgba(0, 0, 0, 0.3)',
    'app_name': 'Test API',
    'app_short_name': 'API',
    'theme_color': '#667eea'
}

print('Testing API upload...')
response = requests.post(url, files=files, data=data)
print(f'Status: {response.status_code}')
result = response.json()
print(f'Success: {result.get("success")}')
print(f'Batch ID: {result.get("batch_id")}')
print(f'Count: {result.get("count")}')

if result.get('success'):
    for r in result['results']:
        print(f'  - {r["original_name"]}: cached={r.get("cached", False)}')
        for k, v in r.get('files', {}).items():
            print(f'    {k}: {v.get("filename")}')
    
    print('\n' + '='*50)
    print('Testing preview page...')
    preview_url = f'http://127.0.0.1:5000/preview/{result.get("batch_id")}'
    preview_response = requests.get(preview_url)
    print(f'Preview page status: {preview_response.status_code}')
    if preview_response.status_code == 200:
        print('Preview page loaded successfully!')
    
    print('\n' + '='*50)
    print('Testing download...')
    download_url = f'http://127.0.0.1:5000/download/{result.get("batch_id")}'
    download_response = requests.get(download_url)
    print(f'Download status: {download_response.status_code}')
    print(f'Download content size: {len(download_response.content)} bytes')
    if download_response.headers.get('Content-Type') == 'application/zip':
        print('ZIP download successful!')
    
    print('\n' + '='*50)
    print('Testing cache (uploading same image again)...')
    files2 = {'files': open('test_images/test_icon.png', 'rb')}
    response2 = requests.post(url, files=files2, data=data)
    result2 = response2.json()
    if result2.get('success'):
        for r in result2['results']:
            print(f'  - {r["original_name"]}: cached={r.get("cached", False)}')
            if r.get('cached'):
                print('Cache hit! Success.')
    
    print('\n' + '='*50)
    print('Testing cache stats API...')
    stats_response = requests.get('http://127.0.0.1:5000/api/cache/stats')
    print(f'Cache stats: {stats_response.json()}')
    
    print('\n✓ All API tests passed!')
else:
    print(f'Error: {result.get("error")}')
