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

    if (typeof results !== 'undefined' && Array.isArray(results)) {
        const appName = (options && options.app_name) || 'My App';
        const appShortName = (options && options.app_short_name) || 'App';
        const themeColor = (options && options.theme_color) || '#ffffff';
        const bgColorManifest = (options && options.background_color_manifest) || themeColor;
        
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
