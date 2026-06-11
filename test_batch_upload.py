from PIL import Image
import os

if not os.path.exists('test_batch1.png'):
    Image.new('RGB', (400, 300), '#ff6b6b').save('test_batch1.png')
if not os.path.exists('test_batch2.png'):
    Image.new('RGB', (300, 400), '#4ecdc4').save('test_batch2.png')

import requests
with open('test_batch1.png', 'rb') as f1, open('test_batch2.png', 'rb') as f2:
    r = requests.post(
        'http://127.0.0.1:5000/upload',
        files=[('files', ('a_red.png', f1)), ('files', ('b_teal.png', f2))]
    )
print('upload_id:', r.json().get('upload_id'))
print('redirect crop:', r.json().get('redirect'))
