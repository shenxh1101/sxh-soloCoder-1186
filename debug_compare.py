import requests
import re

r = requests.get('http://127.0.0.1:5000/history')
ids = re.findall(r'data-id="([a-f0-9\-]+)"', r.text)
print(f'找到 {len(ids)} 条记录，取前3条: {ids[:3]}')

url = 'http://127.0.0.1:5000/compare?ids=' + ','.join(ids[:3])
print('URL:', url)
r2 = requests.get(url)
print(f'对比页 status={r2.status_code}, len={len(r2.text)}')
print('包含 compare-card:', 'compare-card' in r2.text)
print('compare-card 数量:', r2.text.count('compare-card'))
print('包含 ♻️ 套用:', '套用此配置' in r2.text)
# 打印前1500字符方便排查
print('\n--- head ---')
print(r2.text[:2500])
