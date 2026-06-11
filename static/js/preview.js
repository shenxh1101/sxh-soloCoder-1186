document.addEventListener('DOMContentLoaded', function() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    tabBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const tabName = this.getAttribute('data-tab');
            
            tabBtns.forEach(b => b.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));
            
            this.classList.add('active');
            const content = document.querySelector(`[data-content="${tabName}"]`);
            if (content) {
                content.classList.add('active');
            }
        });
    });

    const appName = (options && options.app_name) || 'My App';
    const appShortName = (options && options.app_short_name) || 'App';
    const themeColor = (options && options.theme_color) || '#ffffff';
    const bgColorManifest = (options && options.background_color_manifest) || themeColor;

    const safeAppName = (appName || 'icons').replace(/[^a-zA-Z0-9-_]/g, '') || 'icons';
    const zipInput = document.getElementById('zipName');
    if (zipInput) {
        zipInput.placeholder = `${safeAppName}_icons.zip`;
    }

    initDownloadFilter();

    if (typeof results !== 'undefined' && Array.isArray(results)) {
        results.forEach((result, index) => {
            if (result.error) return;
            
            const manifestCode = document.getElementById(`manifest_${index}`);
            const browserconfigCode = document.getElementById(`browserconfig_${index}`);
            
            if (manifestCode && result.files) {
                const androidIcons = [];
                Object.keys(result.files).forEach(key => {
                    const file = result.files[key];
                    if (file.type === 'android-chrome' && file.size) {
                        androidIcons.push({
                            src: file.filename,
                            sizes: `${file.size[0]}x${file.size[1]}`,
                            type: 'image/png',
                            purpose: 'any maskable'
                        });
                    }
                });
                
                const manifest = {
                    name: appName,
                    short_name: appShortName,
                    icons: androidIcons,
                    theme_color: themeColor,
                    background_color: bgColorManifest,
                    display: 'standalone'
                };
                
                manifestCode.textContent = JSON.stringify(manifest, null, 2);
            }
            
            if (browserconfigCode && result.files) {
                let mstileFilename = 'mstile-150x150.png';
                Object.keys(result.files).forEach(key => {
                    const file = result.files[key];
                    if (file.type === 'mstile') {
                        mstileFilename = file.filename;
                    }
                });
                
                const browserconfig = `<?xml version="1.0" encoding="utf-8"?>
<browserconfig>
    <msapplication>
        <tile>
            <square150x150logo src="${mstileFilename}"/>
            <TileColor>${themeColor}</TileColor>
        </tile>
    </msapplication>
</browserconfig>`;
                
                browserconfigCode.textContent = browserconfig;
            }
        });
    }
});

function initDownloadFilter() {
    if (typeof results === 'undefined' || !Array.isArray(results)) return;
    const result = results.find(r => !r.error);
    if (!result) return;

    const containers = {
        'favicon': document.getElementById('filterFavicon'),
        'apple-touch-icon': document.getElementById('filterApple'),
        'android-chrome': document.getElementById('filterAndroid'),
        'mstile': document.getElementById('filterMstile'),
        'custom': document.getElementById('filterCustom')
    };

    Object.values(containers).forEach(c => { if (c) c.innerHTML = ''; });

    Object.keys(result.files).forEach(key => {
        const file = result.files[key];
        const container = containers[file.type];
        if (!container) return;

        const sizeText = file.size ? `${file.size[0]}×${file.size[1]}` : '多尺寸';
        const item = document.createElement('label');
        item.className = 'filter-item';
        item.innerHTML = `
            <input type="checkbox" data-filename="${file.filename}" checked>
            <span title="${file.filename}">${file.filename}</span>
            <span style="color:#94a3b8;margin-left:auto;font-size:11px;">${sizeText}</span>
        `;
        container.appendChild(item);
    });

    Object.keys(containers).forEach(type => {
        const el = containers[type];
        if (!el || el.children.length === 0) {
            const parent = el.closest('.filter-group');
            if (parent) parent.style.display = 'none';
        }
    });
}

function selectPreset(preset) {
    const boxes = document.querySelectorAll('#downloadFilter input[type="checkbox"][data-filename]');
    boxes.forEach(cb => {
        const fn = cb.dataset.filename;
        let shouldCheck = false;
        switch (preset) {
            case 'all': shouldCheck = true; break;
            case 'none': shouldCheck = false; break;
            case 'favicon':
                shouldCheck = fn.includes('favicon');
                break;
            case 'mobile':
                shouldCheck = fn.includes('apple') || fn.includes('android') || fn.includes('mstile') || fn.includes('touch');
                break;
        }
        cb.checked = shouldCheck;
    });
}

function downloadFiltered() {
    const boxes = document.querySelectorAll('#downloadFilter input[type="checkbox"][data-filename]:checked');
    const files = Array.from(boxes).map(cb => cb.dataset.filename);

    if (files.length === 0) {
        alert('请至少选择一个文件');
        return;
    }

    const includeManifest = document.getElementById('includeManifest').checked;
    const includeBrowserconfig = document.getElementById('includeBrowserconfig').checked;
    const includeHtml = document.getElementById('includeHtml').checked;

    const customName = document.getElementById('zipName').value.trim();

    const formData = new FormData();
    files.forEach(f => formData.append('files', f));
    formData.append('include_manifest', includeManifest);
    formData.append('include_browserconfig', includeBrowserconfig);
    formData.append('include_html', includeHtml);
    if (customName) formData.append('zip_name', customName);

    const url = typeof batch_id !== 'undefined' ? 
        `/download/filtered/${batch_id}` : 
        `/download/filtered/${window.location.pathname.split('/').pop()}`;

    const batchIdFromUrl = window.location.pathname.match(/preview\/([^/]+)/);
    const finalBatchId = (typeof batch_id !== 'undefined') ? batch_id : (batchIdFromUrl ? batchIdFromUrl[1] : '');

    fetch(`/download/filtered/${finalBatchId}`, {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (!response.ok) throw new Error('下载失败');
        const disposition = response.headers.get('Content-Disposition') || '';
        const match = disposition.match(/filename\*?=UTF-8''([^;]+)|filename="?([^"]+)"?/i);
        let downloadName = match ? (decodeURIComponent(match[1] || match[2] || 'icons.zip')) : 'icons.zip';

        return response.blob().then(blob => ({ blob, downloadName }));
    })
    .then(({ blob, downloadName }) => {
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = downloadName;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        setTimeout(() => URL.revokeObjectURL(link.href), 1000);
    })
    .catch(err => {
        alert('下载失败: ' + err.message);
    });
}

function copyCode(button) {
    const codeElement = button.parentElement.querySelector('code') || 
                        button.previousElementSibling.querySelector('code') ||
                        button.parentElement.parentElement.querySelector('code');
    
    if (!codeElement) return;
    
    const text = codeElement.textContent;
    
    navigator.clipboard.writeText(text).then(() => {
        const originalText = button.textContent;
        button.textContent = '✓ 已复制';
        button.style.background = '#2ed573';
        
        setTimeout(() => {
            button.textContent = originalText;
            button.style.background = '';
        }, 2000);
    }).catch(err => {
        const textarea = document.createElement('textarea');
        textarea.value = text;
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);
        
        const originalText = button.textContent;
        button.textContent = '✓ 已复制';
        button.style.background = '#2ed573';
        
        setTimeout(() => {
            button.textContent = originalText;
            button.style.background = '';
        }, 2000);
    });
}
