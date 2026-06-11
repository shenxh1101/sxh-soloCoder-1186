document.addEventListener('DOMContentLoaded', function() {
    const cropCanvas = document.getElementById('cropCanvas');
    const cropFrame = document.getElementById('cropFrame');
    const originalImage = document.getElementById('originalImage');
    const scaleSlider = document.getElementById('scaleSlider');
    const scaleValue = document.getElementById('scaleValue');
    const cropWidthInput = document.getElementById('cropWidth');
    const cropHeightInput = document.getElementById('cropHeight');
    const lockRatioBtn = document.getElementById('lockRatio');
    const modeButtons = document.querySelectorAll('.mode-btn');
    const presetButtons = document.querySelectorAll('.preset-btn');
    const applyCropBtn = document.getElementById('applyCropBtn');
    const skipCropBtn = document.getElementById('skipCropBtn');
    const previewSquare = document.getElementById('previewSquare');
    const preview16 = document.getElementById('preview16');
    const preview32 = document.getElementById('preview32');
    const preview48 = document.getElementById('preview48');
    const preview128 = document.getElementById('preview128');
    
    let isDragging = false;
    let isResizing = false;
    let currentHandle = null;
    let startX, startY;
    let startFrameX, startFrameY, startFrameW, startFrameH;
    let scale = 1.0;
    let cropMode = 'cover';
    let lockRatio = true;
    let aspectRatio = 1;
    
    let imageDisplayW = 0;
    let imageDisplayH = 0;
    
    function init() {
        updateScaleDisplay();
        updatePreview();
        initCropFrame();
        bindEvents();
    }
    
    function initCropFrame() {
        const imgRect = originalImage.getBoundingClientRect();
        imageDisplayW = imgRect.width;
        imageDisplayH = imgRect.height;
        
        const minSize = Math.min(imageDisplayW, imageDisplayH) * 0.6;
        const frameSize = minSize;
        
        const x = (imageDisplayW - frameSize) / 2;
        const y = (imageDisplayH - frameSize) / 2;
        
        cropFrame.style.left = x + 'px';
        cropFrame.style.top = y + 'px';
        cropFrame.style.width = frameSize + 'px';
        cropFrame.style.height = frameSize + 'px';
        
        cropWidthInput.value = Math.round(frameSize / scale);
        cropHeightInput.value = Math.round(frameSize / scale);
    }
    
    function bindEvents() {
        scaleSlider.addEventListener('input', function() {
            scale = parseFloat(this.value);
            updateScaleDisplay();
            updatePreview();
        });
        
        cropWidthInput.addEventListener('change', function() {
            const w = parseInt(this.value) || 16;
            const h = parseInt(cropHeightInput.value) || 16;
            
            if (lockRatio) {
                const newH = Math.round(w / aspectRatio);
                cropHeightInput.value = newH;
                updateFrameFromInputs(w, newH);
            } else {
                updateFrameFromInputs(w, h);
            }
            updatePreview();
        });
        
        cropHeightInput.addEventListener('change', function() {
            const w = parseInt(cropWidthInput.value) || 16;
            const h = parseInt(this.value) || 16;
            
            if (lockRatio) {
                const newW = Math.round(h * aspectRatio);
                cropWidthInput.value = newW;
                updateFrameFromInputs(newW, h);
            } else {
                updateFrameFromInputs(w, h);
            }
            updatePreview();
        });
        
        lockRatioBtn.addEventListener('click', function() {
            lockRatio = !lockRatio;
            this.classList.toggle('active', lockRatio);
            this.textContent = lockRatio ? '🔒' : '🔓';
            if (lockRatio) {
                aspectRatio = parseInt(cropWidthInput.value) / parseInt(cropHeightInput.value);
            }
        });
        
        modeButtons.forEach(btn => {
            btn.addEventListener('click', function() {
                modeButtons.forEach(b => b.classList.remove('active'));
                this.classList.add('active');
                cropMode = this.dataset.mode;
                updatePreview();
            });
        });
        
        presetButtons.forEach(btn => {
            btn.addEventListener('click', function() {
                presetButtons.forEach(b => b.classList.remove('active'));
                this.classList.add('active');
                
                const ratioStr = this.dataset.ratio;
                const [rw, rh] = ratioStr.split(':').map(Number);
                aspectRatio = rw / rh;
                
                const currentW = parseInt(cropWidthInput.value) || 512;
                const newH = Math.round(currentW / aspectRatio);
                cropHeightInput.value = newH;
                updateFrameFromInputs(currentW, newH);
                updatePreview();
            });
        });
        
        cropFrame.addEventListener('mousedown', function(e) {
            if (e.target.classList.contains('handle')) {
                isResizing = true;
                currentHandle = e.target.dataset.handle;
            } else {
                isDragging = true;
            }
            
            const rect = cropFrame.getBoundingClientRect();
            const canvasRect = cropCanvas.getBoundingClientRect();
            
            startX = e.clientX;
            startY = e.clientY;
            startFrameX = rect.left - canvasRect.left;
            startFrameY = rect.top - canvasRect.top;
            startFrameW = rect.width;
            startFrameH = rect.height;
            
            e.preventDefault();
        });
        
        document.addEventListener('mousemove', function(e) {
            if (isDragging) {
                const dx = e.clientX - startX;
                const dy = e.clientY - startY;
                
                let newX = startFrameX + dx;
                let newY = startFrameY + dy;
                
                newX = Math.max(0, Math.min(newX, imageDisplayW - startFrameW));
                newY = Math.max(0, Math.min(newY, imageDisplayH - startFrameH));
                
                cropFrame.style.left = newX + 'px';
                cropFrame.style.top = newY + 'px';
                
                updateInputsFromFrame();
                updatePreview();
            }
            
            if (isResizing && currentHandle) {
                const dx = e.clientX - startX;
                const dy = e.clientY - startY;
                
                let newX = startFrameX;
                let newY = startFrameY;
                let newW = startFrameW;
                let newH = startFrameH;
                
                if (currentHandle.includes('e')) {
                    newW = Math.max(20, startFrameW + dx);
                    if (lockRatio) {
                        newH = newW / aspectRatio;
                    }
                }
                if (currentHandle.includes('w')) {
                    newW = Math.max(20, startFrameW - dx);
                    newX = startFrameX + startFrameW - newW;
                    if (lockRatio) {
                        newH = newW / aspectRatio;
                        newY = startFrameY + startFrameH / 2 - newH / 2;
                    }
                }
                if (currentHandle.includes('s')) {
                    newH = Math.max(20, startFrameH + dy);
                    if (lockRatio) {
                        newW = newH * aspectRatio;
                    }
                }
                if (currentHandle.includes('n')) {
                    newH = Math.max(20, startFrameH - dy);
                    newY = startFrameY + startFrameH - newH;
                    if (lockRatio) {
                        newW = newH * aspectRatio;
                        newX = startFrameX + startFrameW / 2 - newW / 2;
                    }
                }
                
                if (newX < 0) newX = 0;
                if (newY < 0) newY = 0;
                if (newX + newW > imageDisplayW) newW = imageDisplayW - newX;
                if (newY + newH > imageDisplayH) newH = imageDisplayH - newY;
                
                cropFrame.style.left = newX + 'px';
                cropFrame.style.top = newY + 'px';
                cropFrame.style.width = newW + 'px';
                cropFrame.style.height = newH + 'px';
                
                updateInputsFromFrame();
                updatePreview();
            }
        });
        
        document.addEventListener('mouseup', function() {
            isDragging = false;
            isResizing = false;
            currentHandle = null;
        });
        
        applyCropBtn.addEventListener('click', function() {
            applyCropAndGenerate();
        });
        
        skipCropBtn.addEventListener('click', function() {
            skipAndGenerate();
        });
        
        window.addEventListener('resize', function() {
            initCropFrame();
            updatePreview();
        });
        
        if (originalImage.complete) {
            initCropFrame();
            updatePreview();
        } else {
            originalImage.addEventListener('load', function() {
                initCropFrame();
                updatePreview();
            });
        }
    }
    
    function updateScaleDisplay() {
        scaleValue.textContent = Math.round(scale * 100) + '%';
    }
    
    function updateFrameFromInputs(w, h) {
        const displayW = w * scale;
        const displayH = h * scale;
        
        const currentLeft = parseFloat(cropFrame.style.left) || 0;
        const currentTop = parseFloat(cropFrame.style.top) || 0;
        
        const newLeft = Math.min(currentLeft, imageDisplayW - displayW);
        const newTop = Math.min(currentTop, imageDisplayH - displayH);
        
        cropFrame.style.left = Math.max(0, newLeft) + 'px';
        cropFrame.style.top = Math.max(0, newTop) + 'px';
        cropFrame.style.width = displayW + 'px';
        cropFrame.style.height = displayH + 'px';
    }
    
    function updateInputsFromFrame() {
        const w = Math.round(parseFloat(cropFrame.style.width) / scale);
        const h = Math.round(parseFloat(cropFrame.style.height) / scale);
        cropWidthInput.value = w;
        cropHeightInput.value = h;
    }
    
    function getCropParams() {
        const frameLeft = parseFloat(cropFrame.style.left) || 0;
        const frameTop = parseFloat(cropFrame.style.top) || 0;
        const frameW = parseFloat(cropFrame.style.width) || 0;
        const frameH = parseFloat(cropFrame.style.height) || 0;
        
        const imgRect = originalImage.getBoundingClientRect();
        const canvasRect = cropCanvas.getBoundingClientRect();
        const offsetX = imgRect.left - canvasRect.left;
        const offsetY = imgRect.top - canvasRect.top;
        
        const actualX = Math.round((frameLeft - offsetX) / scale);
        const actualY = Math.round((frameTop - offsetY) / scale);
        const actualW = Math.round(frameW / scale);
        const actualH = Math.round(frameH / scale);
        
        return {
            x: Math.max(0, actualX),
            y: Math.max(0, actualY),
            width: Math.max(1, actualW),
            height: Math.max(1, actualH),
            scale: scale,
            mode: cropMode
        };
    }
    
    function updatePreview() {
        const params = getCropParams();
        
        const previewUrl = `/api/crop-image/${uploadId}?x=${params.x}&y=${params.y}&width=${params.width}&height=${params.height}&scale=${params.scale}&mode=${params.mode}&preview_size=256`;
        
        previewSquare.src = previewUrl;
        preview16.src = previewUrl;
        preview32.src = previewUrl;
        preview48.src = previewUrl;
        preview128.src = previewUrl;
    }
    
    function applyCropAndGenerate() {
        const params = getCropParams();
        
        const formData = new FormData();
        formData.append('upload_id', uploadId);
        formData.append('crop_enabled', 'true');
        formData.append('crop_x', params.x);
        formData.append('crop_y', params.y);
        formData.append('crop_width', params.width);
        formData.append('crop_height', params.height);
        formData.append('crop_scale', params.scale);
        formData.append('crop_mode', params.mode);
        
        const url = `/generate`;
        
        showLoading('正在生成图标...');
        
        fetch(url, {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                window.location.href = data.preview_url;
            } else {
                hideLoading();
                alert('生成失败: ' + data.error);
            }
        })
        .catch(error => {
            hideLoading();
            alert('错误: ' + error.message);
        });
    }
    
    function skipAndGenerate() {
        const formData = new FormData();
        formData.append('upload_id', uploadId);
        
        showLoading('正在生成图标...');
        
        fetch('/generate', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                window.location.href = data.preview_url;
            } else {
                hideLoading();
                alert('生成失败: ' + data.error);
            }
        })
        .catch(error => {
            hideLoading();
            alert('错误: ' + error.message);
        });
    }
    
    function showLoading(text) {
        const overlay = document.createElement('div');
        overlay.id = 'loadingOverlay';
        overlay.style.cssText = 'position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.7);display:flex;align-items:center;justify-content:center;z-index:9999;';
        overlay.innerHTML = `
            <div style="background:white;padding:40px 60px;border-radius:15px;text-align:center;">
                <div style="width:50px;height:50px;border:4px solid #f3f3f3;border-top:4px solid #667eea;border-radius:50%;animation:spin 1s linear infinite;margin:0 auto 20px;"></div>
                <h3 style="margin:0;color:#333;">${text}</h3>
            </div>
            <style>@keyframes spin{0%{transform:rotate(0deg)}100%{transform:rotate(360deg)}}</style>
        `;
        document.body.appendChild(overlay);
    }
    
    function hideLoading() {
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) {
            overlay.remove();
        }
    }
    
    init();
});
