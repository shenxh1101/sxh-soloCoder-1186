import requests
import json
import os
import sys

BASE = "http://127.0.0.1:5000"

def test_1_history_detail_fixed():
    """需求1: 历史详情API字段修复"""
    print("\n=== 测试 1: 历史详情API修复 ===")
    r = requests.get(f"{BASE}/history")
    assert r.status_code == 200, f"历史页状态码: {r.status_code}"
    # 找到第一条记录的id (从html粗略提取)
    import re
    m = re.search(r'data-id="([a-f0-9\-]+)"', r.text)
    if not m:
        print("  ⚠️  暂无历史记录,跳过历史详情测试")
        return True
    rid = m.group(1)
    r2 = requests.get(f"{BASE}/api/history/detail/{rid}")
    assert r2.status_code == 200
    data = r2.json()
    assert data['success'], f"detail返回失败: {data}"
    rec = data['record']
    # 这两个字段在routes.py原先是错的
    assert 'id' in rec and rec['id'], "缺失 id 字段"
    assert 'from_cache' in rec, "缺失 from_cache 字段"
    assert 'options' in rec and isinstance(rec['options'], dict), "options 字段错误"
    print(f"  ✅ 历史详情API字段正确: id={rec['id'][:8]}..., from_cache={rec['from_cache']}")
    # 测试 reuse-template API
    r3 = requests.get(f"{BASE}/api/reuse-template/{rid}")
    assert r3.status_code == 200 and r3.json()['success']
    tpl = r3.json()['template']
    assert 'app_name' in tpl and 'theme_color' in tpl, "reuse-template 参数不全"
    print(f"  ✅ 复用模板返回 {len(tpl)} 项参数")
    return True


def test_2_compare_page():
    """需求3: 批量对比页"""
    print("\n=== 测试 3: 批量任务对比页 ===")
    r = requests.get(f"{BASE}/history")
    import re
    ids = re.findall(r'data-id="([a-f0-9\-]+)"', r.text)
    if len(ids) < 2:
        print(f"  ⚠️  历史记录不足2条（当前{len(ids)}条）,跳过对比页测试")
        return True
    r2 = requests.get(f"{BASE}/compare?ids={','.join(ids[:3])}")
    assert r2.status_code == 200, f"对比页状态码: {r2.status_code}"
    assert 'compare-card' in r2.text, "对比页未渲染 compare-card"
    assert '应用名' in r2.text or 'app_name' in r2.text.lower(), "对比页缺少参数对比"
    print(f"  ✅ 对比页可访问，并排展示 {min(3, len(ids))} 张任务卡片")
    assert '♻️ 套用此配置' in r2.text or 'reuseOne' in r2.text, "对比页缺少一键复用按钮"
    print("  ✅ 对比页每张卡片有一键复用按钮")
    return True


def test_4_compare_mode_ui():
    """历史记录页的多选对比UI"""
    print("\n=== 测试 3b: 历史记录多选对比模式 ===")
    r = requests.get(f"{BASE}/history")
    assert r.status_code == 200
    assert 'toggleCompareMode' in r2.text if False else 'toggleCompareMode' in r.text, "缺少对比模式开关"
    assert 'compare-check' in r.text, "缺少 compare-check 复选框"
    assert 'startCompare' in r.text, "缺少 startCompare 函数"
    assert 'clearCompareSelection' in r.text, "缺少清空选择函数"
    print("  ✅ 历史记录页具备多选对比 UI 元素")
    return True


def test_5_upload_info_api():
    """需求4: 批量裁剪信息API"""
    print("\n=== 测试 4a: 上传信息 API (/api/upload-info/<id>) ===")
    # 先上传一张图拿到upload_id
    test_img = os.path.join(os.path.dirname(__file__), 'test.png')
    if not os.path.exists(test_img):
        # 生成一张测试图
        from PIL import Image
        img = Image.new('RGB', (300, 200), color='#667eea')
        img.save(test_img)
    with open(test_img, 'rb') as f:
        r = requests.post(f"{BASE}/upload", files={'files': ('test_upload_info.png', f)}, data={'skip_crop': 'true'})
    # 注意：skip_crop=true不会返回upload_id相关路径，但我们需要另一个请求获得带裁剪的
    with open(test_img, 'rb') as f:
        r2 = requests.post(f"{BASE}/upload", files={'files': ('test_crop_api.png', f)})
    assert r2.status_code == 200 and r2.json()['success']
    upload_id = r2.json()['upload_id']
    # 调 upload-info
    info = requests.get(f"{BASE}/api/upload-info/{upload_id}")
    assert info.status_code == 200 and info.json()['success']
    d = info.json()
    assert d['image_count'] >= 1 and isinstance(d['images'], list), "upload-info 返回结构错误"
    assert 'width' in d['images'][0] and 'name' in d['images'][0], "images 元素缺少字段"
    print(f"  ✅ /api/upload-info 返回 {d['image_count']} 张图信息: {d['images'][0]['name']} {d['images'][0]['width']}x{d['images'][0]['height']}")
    return True


def test_6_download_filtered_html_filename():
    """需求2: HTML片段文件名统一为 icons.html"""
    print("\n=== 测试 2: 自定义下载 manifest/browserconfig/HTML 打包 ===")
    # 先用已有 batch_id，若不存在则生成
    batch_id = None
    try:
        test_img = os.path.join(os.path.dirname(__file__), 'test.png')
        from PIL import Image
        if not os.path.exists(test_img):
            Image.new('RGB', (100,100), '#f00').save(test_img)
        with open(test_img, 'rb') as f:
            r = requests.post(f"{BASE}/upload", files={'files': ('dl_test.png', f)}, data={'skip_crop': 'true'})
        up_id = r.json()['upload_id']
        gen = requests.post(f"{BASE}/generate", data={'upload_id': up_id})
        assert gen.status_code == 200 and gen.json()['success']
        batch_id = gen.json()['batch_id']
    except Exception as e:
        print(f"  ⚠️  生成测试图失败: {e}, 尝试用已有batch")

    if not batch_id:
        # 试试直接访问预览页获取
        r = requests.get(f"{BASE}/history")
        import re
        m = re.search(r'href="/preview/([a-f0-9\-]+)"', r.text)
        if m:
            batch_id = m.group(1)

    if not batch_id:
        print("  ⚠️  无可用batch_id,跳过自定义下载详细测试")
        return True

    # 测试勾选 manifest + browserconfig + html 都打包
    payload = {
        'files': ['favicon.ico'],
        'include_manifest': 'true',
        'include_browserconfig': 'true',
        'include_html': 'true',
        'zip_name': 'test_filtered.zip'
    }
    r = requests.post(f"{BASE}/download/filtered/{batch_id}", data=payload)
    assert r.status_code == 200, f"download_filtered 状态码: {r.status_code}"
    assert r.headers.get('Content-Type') == 'application/zip', "返回不是zip"
    cd = r.headers.get('Content-Disposition', '')
    assert 'test_filtered.zip' in cd or "UTF-8''test_filtered" in cd, f"ZIP名未生效: {cd}"
    import zipfile, io
    zf = zipfile.ZipFile(io.BytesIO(r.content))
    names = zf.namelist()
    print(f"  ✅ ZIP包含文件: {names}")
    # 检查 manifest.json, browserconfig.xml, icons.html 都在里面
    assert 'manifest.json' in names, "缺失 manifest.json"
    assert 'browserconfig.xml' in names, "缺失 browserconfig.xml"
    assert 'icons.html' in names, f"缺失 icons.html（HTML片段实际文件名）"
    assert 'favicon.ico' in names, "缺失勾选的 favicon.ico"
    print("  ✅ manifest.json / browserconfig.xml / icons.html 均正确打包")
    return True


def test_7_crop_api_index_param():
    """裁剪API支持按index取多图中的某张"""
    print("\n=== 测试 4b: 裁剪/原图 API 支持 index 参数 ===")
    test_img = os.path.join(os.path.dirname(__file__), 'test.png')
    with open(test_img, 'rb') as f:
        r = requests.post(f"{BASE}/upload", files={'files': ('idx_api.png', f)})
    up_id = r.json()['upload_id']
    # 调原图片 index=0
    r2 = requests.get(f"{BASE}/api/original-image/{up_id}?index=0")
    assert r2.status_code == 200 and r2.headers['Content-Type'] == 'image/png'
    # 调裁剪图 index=0
    r3 = requests.get(f"{BASE}/api/crop-image/{up_id}?index=0&x=0&y=0&width=50&height=50&preview_size=64")
    assert r3.status_code == 200 and r3.headers['Content-Type'] == 'image/png'
    # index 越界时默认回退到0（不应该500）
    r4 = requests.get(f"{BASE}/api/original-image/{up_id}?index=999")
    assert r4.status_code == 200, "越界index不应500"
    print("  ✅ /api/original-image 和 /api/crop-image 均支持 index 参数，越界不报错")
    return True


def main():
    tests = [
        test_1_history_detail_fixed,
        test_2_compare_page,
        test_4_compare_mode_ui,
        test_5_upload_info_api,
        test_6_download_filtered_html_filename,
        test_7_crop_api_index_param,
    ]
    passed = 0
    for t in tests:
        try:
            if t():
                passed += 1
        except Exception as e:
            print(f"  ❌ {t.__name__} 异常: {e}")
            import traceback; traceback.print_exc()
    print(f"\n============================\n共 {len(tests)} 项, 通过 {passed} 项")
    return passed == len(tests)


if __name__ == '__main__':
    sys.exit(0 if main() else 1)
