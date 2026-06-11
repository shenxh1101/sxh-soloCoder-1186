document.addEventListener('DOMContentLoaded', function() {
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');
    const fileList = document.getElementById('fileList');
    const generateBtn = document.getElementById('generateBtn');
    const progressOverlay = document.getElementById('progressOverlay');
    const progressTitle = document.getElementById('progressTitle');
    const progressText = document.getElementById('progressText');

    const cornerRadiusSlider = document.getElementById('cornerRadius');
    const cornerRadiusValue = document.getElementById('cornerRadiusValue');
    const transparentBg = document.getElementById('transparentBg');
    const backgroundColor = document.getElementById('backgroundColor');
    const backgroundColorText = document.getElementById('backgroundColorText');
    const shadowCheckbox = document.getElementById('shadow');
    const shadowOptions = document.getElementById('shadowOptions');
    const shadowBlur = document.getElementById('shadowBlur');
    const shadowBlurValue = document.getElementById('shadowBlurValue');
    const shadowColor = document.getElementById('shadowColor');
    const shadowOpacity = document.getElementById('shadowOpacity');

    const toggleSizesBtn = document.getElementById('toggleSizes');
    const sizesOptions = document.getElementById('sizesOptions');
    const standardSizeList = document.getElementById('standardSizeList');
    const customSizeList = document.getElementById('customSizeList');
    const addCustomSizeBtn = document.getElementById('addCustomSizeBtn');
    const addSizeRow = document.getElementById('addSizeRow');
    const newSizeW = document.getElementById('newSizeW');
    const newSizeH = document.getElementById('newSizeH');
    const newSizeSquare = document.getElementById('newSizeSquare');
    const confirmAddSize = document.getElementById('confirmAddSize');
    const cancelAddSize = document.getElementById('cancelAddSize');

    const enableCrop = document.getElementById('enableCrop');

    const appName = document.getElementById('appName');
    const appShortName = document.getElementById('appShortName');
    const themeColor = document.getElementById('themeColor');

    let selectedFiles = [];
    let customSizes = [];

    const STANDARD_SIZES = [
        { key: 'favicon', width: 16, height: 16, label: 'Favicon (多尺寸)', defaultFilename: 'favicon.ico', type: 'favicon', isMulti: true },
        { key: 'apple-touch-icon-180x180', width: 180, height: 180, label: 'Apple Touch 180px', defaultFilename: 'apple-touch-icon.png', type: 'apple-touch-icon' },
        { key: 'android-chrome-192x192', width: 192, height: 192, label: 'Android Chrome 192px', defaultFilename: 'android-chrome-192x192.png', type: 'android-chrome' },
        { key: 'android-chrome-512x512', width: 512, height: 512, label: 'Android Chrome 512px', defaultFilename: 'android-chrome-512x512.png', type: 'android-chrome' },
        { key: 'mstile-150x150', width: 150, height: 150, label: 'Windows 磁贴 150px', defaultFilename: 'mstile-150x150.png', type: 'mstile' }
    ];

    let standardFilenames = {};
    STANDARD_SIZES.forEach(s => {
        standardFilenames[s.key] = s.defaultFilename;
    });

    let reuseTemplate = null;

    function init() {
        initFromTemplate();
        renderStandardSizes();
        renderCustomSizes();
        bindEvents();
    }

    function initFromTemplate() {
        const tpl = sessionStorage.getItem('reuseTemplate');
        if (tpl) {
            try {
                reuseTemplate = JSON.parse(tpl);
                sessionStorage.removeItem('reuseTemplate');
                applyTemplate(reuseTemplate);
            } catch(e) {}
        }
    }

    function applyTemplate(tpl) {
        if (tpl.corner_radius !== undefined) {
            cornerRadiusSlider.value = tpl.corner_radius;
            cornerRadiusValue.textContent = tpl.corner_radius + 'px';
        }
        if (tpl.background_color !== undefined && tpl.background_color !== null) {
            transparentBg.checked = false;
            backgroundColor.disabled = false;
            backgroundColorText.disabled = false;
            backgroundColor.value = tpl.background_color;
            backgroundColorText.value = tpl.background_color;
        }
        if (tpl.shadow !== undefined) {
            shadowCheckbox.checked = tpl.shadow;
            shadowOptions.style.display = tpl.shadow ? 'block' : 'none';
        }
        if (tpl.shadow_blur !== undefined) {
            shadowBlur.value = tpl.shadow_blur;
            shadowBlurValue.textContent = tpl.shadow_blur + 'px';
        }
        if (tpl.shadow_offset) {
            document.getElementById('shadowOffsetX').value = tpl.shadow_offset[0] || 0;
            document.getElementById('shadowOffsetY').value = tpl.shadow_offset[1] || 0;
        }
        if (tpl.shadow_color) {
            const m = tpl.shadow_color.match(/rgba?\(([^)]+)\)/);
            if (m) {
                const parts = m[1].split(',').map(s => s.trim());
                const r = parseInt(parts[0]), g = parseInt(parts[1]), b = parseInt(parts[2]);
                shadowColor.value = '#' + [r,g,b].map(v => v.toString(16).padStart(2,'0')).join('');
                shadowOpacity.value = parts[3] || '1.0';
            }
        }
        if (tpl.app_name) appName.value = tpl.app_name;
        if (tpl.app_short_name) appShortName.value = tpl.app_short_name;
        if (tpl.theme_color) themeColor.value = tpl.theme_color;

        if (tpl.custom_filenames) {
            Object.keys(tpl.custom_filenames).forEach(k => {
                if (standardFilenames[k] !== undefined) {
                    standardFilenames[k] = tpl.custom_filenames[k];
                }
            });
        }
        if (tpl.custom_sizes && Array.isArray(tpl.custom_sizes)) {
            customSizes = tpl.custom_sizes.map(sz => {
                const w = Array.isArray(sz) ? sz[0] : sz.width;
                const h = Array.isArray(sz) ? sz[1] || w : sz.height || w;
                const key = `custom-${w}x${h}`;
                return {
                    key: key,
                    width: w,
                    height: h,
                    label: `自定义 ${w}×${h}`,
                    type: 'custom',
                    filename: (tpl.custom_filenames && tpl.custom_filenames[key]) || `custom-${w}x${h}.png`
                };
            });
        }
        renderStandardSizes();
        renderCustomSizes();

        if (tpl.crop && tpl.crop.enabled) {
            sessionStorage.setItem('reuseCrop', JSON.stringify(tpl.crop));
        }
    }

    function renderStandardSizes() {
        standardSizeList.innerHTML = '';
        STANDARD_SIZES.forEach((size, index) => {
            const div = document.createElement('div');
            div.className = 'size-row';
            div.dataset.key = size.key;
            const sizeText = size.isMulti ? '16/32/48' : `${size.width}×${size.height}`;
            div.innerHTML = `
                <div class="size-info">
                    <span class="size-label">${size.label}</span>
                    <span class="size-dim">${sizeText}</span>
                </div>
                <div class="size-filename">
                    <input type="text" class="filename-input" 
                           data-key="${size.key}" 
                           value="${standardFilenames[size.key]}" 
                           placeholder="${size.defaultFilename}">
                </div>
            `;
            standardSizeList.appendChild(div);
        });

        standardSizeList.querySelectorAll('.filename-input').forEach(inp => {
            inp.addEventListener('change', function() {
                standardFilenames[this.dataset.key] = this.value || STANDARD_SIZES.find(s => s.key === this.dataset.key).defaultFilename;
            });
        });
    }

    function renderCustomSizes() {
        customSizeList.innerHTML = '';
        if (customSizes.length === 0) {
            customSizeList.innerHTML = '<div class="empty-hint">暂无自定义尺寸，点击上方「+ 添加尺寸」</div>';
            return;
        }

        customSizes.forEach((size, index) => {
            const div = document.createElement('div');
            div.className = 'size-row custom';
            div.dataset.index = index;
            div.innerHTML = `
                <div class="size-reorder">
                    <button type="button" class="btn-reorder" data-dir="up" title="上移" ${index === 0 ? 'disabled' : ''}>↑</button>
                    <button type="button" class="btn-reorder" data-dir="down" title="下移" ${index === customSizes.length - 1 ? 'disabled' : ''}>↓</button>
                </div>
                <div class="size-info">
                    <span class="size-label">自定义</span>
                    <span class="size-dim">${size.width}×${size.height}</span>
                </div>
                <div class="size-filename">
                    <input type="text" class="filename-input" 
                           data-index="${index}" 
                           value="${size.filename}" 
                           placeholder="custom-${size.width}x${size.height}.png">
                </div>
                <button type="button" class="btn-delete" title="删除">×</button>
            `;
            customSizeList.appendChild(div);
        });

        customSizeList.querySelectorAll('.filename-input').forEach(inp => {
            inp.addEventListener('change', function() {
                const i = parseInt(this.dataset.index);
                if (customSizes[i]) {
                    customSizes[i].filename = this.value || `custom-${customSizes[i].width}x${customSizes[i].height}.png`;
                }
            });
        });

        customSizeList.querySelectorAll('.btn-reorder').forEach(btn => {
            btn.addEventListener('click', function() {
                const i = parseInt(this.closest('.size-row').dataset.index);
                const dir = this.dataset.dir;
                if (dir === 'up' && i > 0) {
                    [customSizes[i], customSizes[i-1]] = [customSizes[i-1], customSizes[i]];
                } else if (dir === 'down' && i < customSizes.length - 1) {
                    [customSizes[i], customSizes[i+1]] = [customSizes[i+1], customSizes[i]];
                }
                renderCustomSizes();
            });
        });

        customSizeList.querySelectorAll('.btn-delete').forEach(btn => {
            btn.addEventListener('click', function() {
                const i = parseInt(this.closest('.size-row').dataset.index);
                customSizes.splice(i, 1);
                renderCustomSizes();
            });
        });
    }

    function bindEvents() {
        uploadArea.addEventListener('click', () => fileInput.click());
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });
        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('dragover');
        });
        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            handleFiles(e.dataTransfer.files);
        });
        fileInput.addEventListener('change', () => handleFiles(fileInput.files));

        cornerRadiusSlider.addEventListener('input', () => {
            cornerRadiusValue.textContent = cornerRadiusSlider.value + 'px';
        });

        transparentBg.addEventListener('change', () => {
            const isTransparent = transparentBg.checked;
            backgroundColor.disabled = isTransparent;
            backgroundColorText.disabled = isTransparent;
            if (isTransparent) {
                backgroundColorText.value = '';
            } else {
                backgroundColorText.value = backgroundColor.value;
            }
        });
        backgroundColor.addEventListener('input', () => {
            if (!transparentBg.checked) {
                backgroundColorText.value = backgroundColor.value;
            }
        });
        backgroundColorText.addEventListener('input', () => {
            if (!transparentBg.checked && backgroundColorText.value) {
                backgroundColor.value = backgroundColorText.value;
            }
        });

        shadowCheckbox.addEventListener('change', () => {
            shadowOptions.style.display = shadowCheckbox.checked ? 'block' : 'none';
        });
        shadowBlur.addEventListener('input', () => {
            shadowBlurValue.textContent = shadowBlur.value + 'px';
        });

        toggleSizesBtn.addEventListener('click', function() {
            if (sizesOptions.style.display === 'none') {
                sizesOptions.style.display = 'block';
                this.textContent = '收起';
            } else {
                sizesOptions.style.display = 'none';
                this.textContent = '展开';
            }
        });

        addCustomSizeBtn.addEventListener('click', () => {
            addSizeRow.style.display = 'flex';
            newSizeW.value = '256';
            newSizeH.value = '256';
            newSizeW.focus();
        });

        newSizeSquare.addEventListener('change', function() {
            if (this.checked) {
                newSizeH.value = newSizeW.value;
            }
        });
        newSizeW.addEventListener('input', function() {
            if (newSizeSquare.checked) {
                newSizeH.value = this.value;
            }
        });

        confirmAddSize.addEventListener('click', () => {
            const w = parseInt(newSizeW.value);
            const h = parseInt(newSizeH.value);
            if (!w || w < 1 || w > 4096) { alert('请输入有效的宽度 (1-4096)'); return; }
            if (!h || h < 1 || h > 4096) { alert('请输入有效的高度 (1-4096)'); return; }

            const key = `custom-${w}x${h}`;
            const exists = customSizes.some(s => s.width === w && s.height === h);
            if (exists) { alert('该尺寸已存在'); return; }

            customSizes.push({
                key: key,
                width: w,
                height: h,
                label: `自定义 ${w}×${h}`,
                type: 'custom',
                filename: `custom-${w}x${h}.png`
            });

            addSizeRow.style.display = 'none';
            renderCustomSizes();
        });

        cancelAddSize.addEventListener('click', () => {
            addSizeRow.style.display = 'none';
        });

        generateBtn.addEventListener('click', startUpload);
    }

    function handleFiles(files) {
        selectedFiles = Array.from(files);
        fileList.innerHTML = '';
        selectedFiles.forEach((file, index) => {
            const div = document.createElement('div');
            div.className = 'file-item';
            div.innerHTML = `
                <span class="file-name">${file.name}</span>
                <span class="file-size">${formatFileSize(file.size)}</span>
                <button type="button" class="remove-file" data-index="${index}">×</button>
            `;
            fileList.appendChild(div);
        });

        fileList.querySelectorAll('.remove-file').forEach(btn => {
            btn.addEventListener('click', () => {
                const i = parseInt(btn.dataset.index);
                selectedFiles.splice(i, 1);
                handleFiles(selectedFiles);
            });
        });

        generateBtn.disabled = selectedFiles.length === 0;
    }

    function formatFileSize(bytes) {
        if (bytes < 1024) return bytes + ' B';
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
        return (bytes / 1024 / 1024).toFixed(1) + ' MB';
    }

    function collectFormData() {
        const fd = new FormData();

        selectedFiles.forEach(file => {
            fd.append('files', file);
        });

        fd.append('corner_radius', cornerRadiusSlider.value);
        if (transparentBg.checked) {
            fd.append('background_color', '');
        } else {
            fd.append('background_color', backgroundColorText.value || backgroundColor.value);
        }
        fd.append('shadow', shadowCheckbox.checked ? 'true' : 'false');
        if (shadowCheckbox.checked) {
            fd.append('shadow_blur', shadowBlur.value);
            fd.append('shadow_offset_x', document.getElementById('shadowOffsetX').value);
            fd.append('shadow_offset_y', document.getElementById('shadowOffsetY').value);
            const sc = shadowColor.value;
            const r = parseInt(sc.slice(1,3),16), g = parseInt(sc.slice(3,5),16), b = parseInt(sc.slice(5,7),16);
            const a = parseFloat(shadowOpacity.value) || 1.0;
            fd.append('shadow_color', `rgba(${r}, ${g}, ${b}, ${a})`);
        }

        STANDARD_SIZES.forEach(s => {
            const fn = standardFilenames[s.key];
            if (fn && fn !== s.defaultFilename) {
                fd.append(`filename_${s.key}`, fn);
            }
        });

        customSizes.forEach(sz => {
            fd.append('custom_sizes[]', `${sz.width}x${sz.height}`);
            if (sz.filename && sz.filename !== `custom-${sz.width}x${sz.height}.png`) {
                fd.append(`filename_custom-${sz.width}x${sz.height}`, sz.filename);
            }
        });

        fd.append('app_name', appName.value);
        fd.append('app_short_name', appShortName.value);
        fd.append('theme_color', themeColor.value);
        fd.append('background_color_manifest', themeColor.value);

        fd.append('enable_crop', enableCrop.checked ? 'true' : 'false');

        return fd;
    }

    function startUpload() {
        if (selectedFiles.length === 0) return;

        progressOverlay.style.display = 'flex';
        progressTitle.textContent = '正在上传...';
        progressText.textContent = '请稍候';

        const formData = collectFormData();

        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (!data.success) {
                hideProgress();
                alert('上传失败: ' + (data.error || '未知错误'));
                return;
            }
            if (enableCrop.checked && !data.skip_crop) {
                window.location.href = `/crop/${data.upload_id}`;
            } else {
                generateDirectly(data.upload_id);
            }
        })
        .catch(error => {
            hideProgress();
            alert('错误: ' + error.message);
        });
    }

    function generateDirectly(uploadId) {
        progressTitle.textContent = '正在生成图标...';
        progressText.textContent = '请稍候，这可能需要几秒钟';

        const genFD = new FormData();
        genFD.append('upload_id', uploadId);
        if (selectedFiles.length > 1 || selectedFiles[0].name.toLowerCase().endsWith('.zip')) {
            genFD.append('batch', 'true');
        }

        fetch('/generate', {
            method: 'POST',
            body: genFD
        })
        .then(response => response.json())
        .then(data => {
            hideProgress();
            if (data.success) {
                window.location.href = data.preview_url;
            } else {
                alert('生成失败: ' + (data.error || '未知错误'));
            }
        })
        .catch(error => {
            hideProgress();
            alert('错误: ' + error.message);
        });
    }

    function hideProgress() {
        progressOverlay.style.display = 'none';
    }

    init();
});
