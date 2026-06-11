document.addEventListener('DOMContentLoaded', function() {
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');
    const fileList = document.getElementById('fileList');
    const generateBtn = document.getElementById('generateBtn');
    const progressOverlay = document.getElementById('progressOverlay');
    const progressText = document.getElementById('progressText');
    const progressTitle = document.getElementById('progressTitle');
    
    const cornerRadius = document.getElementById('cornerRadius');
    const cornerRadiusValue = document.getElementById('cornerRadiusValue');
    const shadowCheckbox = document.getElementById('shadow');
    const shadowOptions = document.getElementById('shadowOptions');
    const shadowBlur = document.getElementById('shadowBlur');
    const shadowBlurValue = document.getElementById('shadowBlurValue');
    const transparentBg = document.getElementById('transparentBg');
    const backgroundColor = document.getElementById('backgroundColor');
    const backgroundColorText = document.getElementById('backgroundColorText');
    const toggleFilenames = document.getElementById('toggleFilenames');
    const filenameOptions = document.getElementById('filenameOptions');
    const enableCrop = document.getElementById('enableCrop');
    
    let selectedFiles = [];
    let filenamesExpanded = false;

    cornerRadius.addEventListener('input', function() {
        cornerRadiusValue.textContent = this.value + 'px';
    });

    shadowBlur.addEventListener('input', function() {
        shadowBlurValue.textContent = this.value + 'px';
    });

    shadowCheckbox.addEventListener('change', function() {
        shadowOptions.style.display = this.checked ? 'block' : 'none';
    });

    transparentBg.addEventListener('change', function() {
        backgroundColor.disabled = this.checked;
        backgroundColorText.disabled = this.checked;
        if (this.checked) {
            backgroundColorText.value = '';
        }
    });

    backgroundColor.addEventListener('input', function() {
        backgroundColorText.value = this.value;
    });

    backgroundColorText.addEventListener('input', function() {
        if (/^#[0-9A-Fa-f]{6}$/.test(this.value)) {
            backgroundColor.value = this.value;
        }
    });

    if (toggleFilenames) {
        toggleFilenames.addEventListener('click', function() {
            filenamesExpanded = !filenamesExpanded;
            filenameOptions.style.display = filenamesExpanded ? 'block' : 'none';
            toggleFilenames.textContent = filenamesExpanded ? '收起' : '展开';
        });
    }

    uploadArea.addEventListener('dragover', function(e) {
        e.preventDefault();
        uploadArea.classList.add('drag-over');
    });

    uploadArea.addEventListener('dragleave', function(e) {
        e.preventDefault();
        uploadArea.classList.remove('drag-over');
    });

    uploadArea.addEventListener('drop', function(e) {
        e.preventDefault();
        uploadArea.classList.remove('drag-over');
        handleFiles(e.dataTransfer.files);
    });

    fileInput.addEventListener('change', function(e) {
        handleFiles(e.target.files);
    });

    function handleFiles(files) {
        const validExtensions = ['png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'zip'];
        
        for (let file of files) {
            const ext = file.name.split('.').pop().toLowerCase();
            if (validExtensions.includes(ext)) {
                if (!selectedFiles.find(f => f.name === file.name && f.size === file.size)) {
                    selectedFiles.push(file);
                }
            }
        }
        
        updateFileList();
        updateGenerateButton();
    }

    function updateFileList() {
        fileList.innerHTML = '';
        
        selectedFiles.forEach((file, index) => {
            const fileItem = document.createElement('div');
            fileItem.className = 'file-item';
            
            const fileName = document.createElement('span');
            fileName.className = 'file-item-name';
            fileName.textContent = `${file.name} (${formatFileSize(file.size)})`;
            
            const removeBtn = document.createElement('button');
            removeBtn.className = 'file-item-remove';
            removeBtn.textContent = '移除';
            removeBtn.onclick = function() {
                selectedFiles.splice(index, 1);
                updateFileList();
                updateGenerateButton();
            };
            
            fileItem.appendChild(fileName);
            fileItem.appendChild(removeBtn);
            fileList.appendChild(fileItem);
        });
    }

    function formatFileSize(bytes) {
        if (bytes < 1024) return bytes + ' B';
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
        return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
    }

    function updateGenerateButton() {
        generateBtn.disabled = selectedFiles.length === 0;
    }

    function collectFormData() {
        const formData = new FormData();
        
        selectedFiles.forEach(file => {
            formData.append('files', file);
        });
        
        formData.append('corner_radius', cornerRadius.value);
        
        if (!transparentBg.checked && backgroundColorText.value) {
            formData.append('background_color', backgroundColorText.value);
        }
        
        formData.append('shadow', shadowCheckbox.checked);
        if (shadowCheckbox.checked) {
            formData.append('shadow_blur', shadowBlur.value);
            formData.append('shadow_offset_x', document.getElementById('shadowOffsetX').value);
            formData.append('shadow_offset_y', document.getElementById('shadowOffsetY').value);
            
            const shadowColor = document.getElementById('shadowColor').value;
            const shadowOpacity = document.getElementById('shadowOpacity').value;
            const r = parseInt(shadowColor.slice(1, 3), 16);
            const g = parseInt(shadowColor.slice(3, 5), 16);
            const b = parseInt(shadowColor.slice(5, 7), 16);
            formData.append('shadow_color', `rgba(${r}, ${g}, ${b}, ${shadowOpacity})`);
        }
        
        formData.append('app_name', document.getElementById('appName').value);
        formData.append('app_short_name', document.getElementById('appShortName').value);
        formData.append('theme_color', document.getElementById('themeColor').value);
        formData.append('background_color_manifest', document.getElementById('themeColor').value);
        
        const customSizes = document.getElementById('customSizes').value;
        if (customSizes) {
            formData.append('custom_sizes', customSizes);
        }
        
        const filenameInputs = document.querySelectorAll('input[name^="filename_"]');
        filenameInputs.forEach(input => {
            if (input.value.trim()) {
                formData.append(input.name, input.value.trim());
            }
        });
        
        return formData;
    }

    generateBtn.addEventListener('click', function() {
        if (selectedFiles.length === 0) return;
        
        const formData = collectFormData();
        
        if (enableCrop && enableCrop.checked) {
            formData.append('skip_crop', 'false');
        } else {
            formData.append('skip_crop', 'true');
        }
        
        progressOverlay.style.display = 'flex';
        progressTitle.textContent = '正在上传...';
        progressText.textContent = '请稍候';
        
        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => { throw new Error(err.error || '上传失败'); });
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                if (data.skip_crop) {
                    progressTitle.textContent = '正在生成图标...';
                    progressText.textContent = '请稍候';
                    
                    const generateFormData = new FormData();
                    generateFormData.append('upload_id', data.upload_id);
                    
                    const allOptions = collectFormData();
                    for (let pair of allOptions.entries()) {
                        if (pair[0] !== 'files') {
                            generateFormData.append(pair[0], pair[1]);
                        }
                    }
                    
                    return fetch('/generate', {
                        method: 'POST',
                        body: generateFormData
                    }).then(r => r.json()).then(d => {
                        if (d.success) {
                            progressText.textContent = '生成成功！正在跳转到预览页面...';
                            setTimeout(() => {
                                window.location.href = d.preview_url;
                            }, 500);
                        } else {
                            throw new Error(d.error || '生成失败');
                        }
                    });
                } else {
                    progressText.textContent = '上传成功！正在跳转到裁剪页面...';
                    setTimeout(() => {
                        window.location.href = data.crop_url;
                    }, 500);
                }
            } else {
                throw new Error(data.error || '上传失败');
            }
        })
        .catch(error => {
            progressOverlay.style.display = 'none';
            alert('错误: ' + error.message);
        });
    });
});

function copyCode(button) {
    const codeElement = button.parentElement.nextElementSibling.querySelector('code') || 
                        button.previousElementSibling.querySelector('code');
    
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
