let stagedFile = null;
let isMirrorActive = false;

function switchTab(tabId) {
    document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.view').forEach(el => el.classList.remove('active'));
    event.currentTarget.classList.add('active');
    document.getElementById('view-' + tabId).classList.add('active');
    if(tabId === 'logs') loadLogs();
    if(tabId === 'gallery') loadGallery();
    if(tabId === 'alerts') loadNotifications();
}

function showToast(msg, type = 'success') {
    const toast = document.getElementById('toast');
    toast.textContent = msg;
    toast.className = 'toast ' + type + ' show';
    setTimeout(() => toast.classList.remove('show'), 3000);
}

function toggleFullscreen() {
    if (!document.fullscreenElement) document.documentElement.requestFullscreen().catch(e => showToast(e.message, 'error'));
    else document.exitFullscreen();
}

async function detectUSB() {
    const res = await fetch('/api/detect_usb');
    const data = await res.json();
    if(data.success) {
        document.getElementById('device-name').textContent = data.model;
        document.getElementById('device-badge').className = 'badge online';
        document.getElementById('conn-type').textContent = 'USB';
        showToast("USB Connected!");
    } else showToast("No USB device found.", 'error');
}

async function connectWiFi() {
    const ip = document.getElementById('ip-input').value;
    if(!ip) return showToast("Enter IP Address", 'error');
    showToast("Connecting...", 'success');
    const res = await fetch('/api/connect_wifi', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ip})});
    const data = await res.json();
    if(data.success) {
        document.getElementById('device-name').textContent = 'Wireless Device';
        document.getElementById('device-badge').className = 'badge online';
        document.getElementById('conn-type').textContent = 'WI-FI';
        showToast("Wi-Fi Connected!", 'success');
    } else showToast("Connection failed.", 'error');
}

async function launchMirror() {
    const audioEnabled = document.getElementById('audio-toggle').checked;
    const res = await fetch('/api/mirror', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({audio: audioEnabled})});
    const data = await res.json();
    if(data.success) {
        showToast(`Launching Mirror (Audio: ${audioEnabled ? 'ON' : 'OFF'})`, 'success');
        isMirrorActive = true;
    } else {
        showToast("Failed to launch. Check System Logs.", 'error');
        isMirrorActive = false;
    }
}

document.getElementById('audio-toggle').addEventListener('change', async (e) => {
    if (isMirrorActive) {
        showToast("Restarting Mirror with new audio settings...", 'success');
        await fetch('/api/stop_mirror', { method: 'POST' }); 
        // INCREASED WAIT TIME TO 2.5 SECONDS
        setTimeout(() => {
            launchMirror();
        }, 2500); 
    }
});

async function takeScreenshot() {
    showToast("Capturing...", 'success');
    const res = await fetch('/api/screenshot', {method: 'POST'});
    const data = await res.json();
    if(data.success) { showToast("Saved to phone.", 'success'); loadGallery(); }
    else showToast("Capture failed.", 'error');
}

async function sendCommand(type) {
    const res = await fetch('/api/command', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({type})});
    const data = await res.json();
    if(data.success) showToast(`Command sent.`, 'success');
    else showToast("Command rejected.", 'error');
}

async function disconnectDevice() {
    showToast("Disconnecting...", 'success');
    const res = await fetch('/api/disconnect', { method: 'POST' });
    const data = await res.json();
    if (data.success) {
        document.getElementById('device-name').textContent = 'No Device';
        document.getElementById('device-badge').className = 'badge offline';
        document.getElementById('conn-type').textContent = 'DISCONNECTED';
        showToast("Device disconnected.", 'success');
        isMirrorActive = false;
    }
}

const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const wizard = document.getElementById('transfer-wizard');

dropZone.addEventListener('dragover', (e) => { e.preventDefault(); dropZone.classList.add('dragover'); });
dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('dragover');
    if(e.dataTransfer.files.length) stageFile(e.dataTransfer.files[0]);
});
fileInput.addEventListener('change', function() {
    if(this.files.length) stageFile(this.files[0]);
});

function stageFile(file) {
    stagedFile = file;
    const sizeMB = (file.size / (1024 * 1024)).toFixed(2);
    const sizeKB = (file.size / 1024).toFixed(2);
    document.getElementById('preview-size').textContent = sizeMB > 0.1 ? `${sizeMB} MB` : `${sizeKB} KB`;
    document.getElementById('preview-name').textContent = file.name;
    const imgPreview = document.getElementById('preview-img');
    const iconPreview = document.getElementById('preview-icon');
    if (file.type.startsWith('image/')) {
        const reader = new FileReader();
        reader.onload = (e) => {
            imgPreview.src = e.target.result;
            imgPreview.classList.remove('hidden');
            iconPreview.classList.add('hidden');
        };
        reader.readAsDataURL(file);
    } else {
        imgPreview.classList.add('hidden');
        iconPreview.classList.remove('hidden');
    }
    dropZone.classList.add('hidden');
    wizard.classList.remove('hidden');
}

function cancelUpload() {
    stagedFile = null;
    fileInput.value = "";
    dropZone.classList.remove('hidden');
    wizard.classList.add('hidden');
}

async function confirmUpload() {
    if(!stagedFile) return;
    const btn = document.getElementById('upload-btn');
    btn.innerHTML = 'Transferring...';
    btn.disabled = true;
    const formData = new FormData();
    formData.append('file', stagedFile);
    try {
        const res = await fetch('/api/upload', { method: 'POST', body: formData });
        const data = await res.json();
        if(data.success) {
            showToast("File pushed to phone Download folder!", 'success');
            cancelUpload();
        } else {
            showToast("Upload failed: " + data.message, 'error');
        }
    } catch(err) {
        showToast("Upload Error: Network failure", 'error');
    } finally {
        btn.innerHTML = '<i data-lucide="send"></i> Transfer';
        btn.disabled = false;
        lucide.createIcons();
    }
}

async function loadNotifications() {
    const container = document.getElementById('alerts-container');
    container.innerHTML = '<p class="empty-state">Fetching notifications...</p>';
    const res = await fetch('/api/notifications');
    const alerts = await res.json();
    if(alerts.length === 0) { container.innerHTML = '<p class="empty-state">No notifications found.</p>'; return; }
    container.innerHTML = '';
    alerts.forEach(a => {
        const div = document.createElement('div');
        div.className = 'alert-card';
        div.innerHTML = `<div class="alert-app">${a.app}</div><div class="alert-title">${a.title || 'No Title'}</div><div class="alert-text">${a.text || 'No Message Body'}</div>`;
        container.appendChild(div);
    });
}

async function loadGallery() {
    const res = await fetch('/api/gallery');
    const images = await res.json();
    const grid = document.getElementById('gallery-grid');
    if(images.length === 0) { grid.innerHTML = '<p class="empty-state">No captures found.</p>'; return; }
    grid.innerHTML = '';
    images.forEach(img => {
        const div = document.createElement('div');
        div.className = 'gallery-item';
        div.innerHTML = `
            <img src="/api/image/${img.filename}" onclick="window.open(this.src)" style="cursor:pointer">
            <div class="gallery-info"><span>${img.time}</span><button class="delete-btn" onclick="deleteImage('${img.filename}')">✕</button></div>
        `;
        grid.appendChild(div);
    });
}

async function deleteImage(filename) {
    if(!confirm("Delete this image?")) return;
    await fetch('/api/delete_capture', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({filename})});
    loadGallery();
}

async function loadLogs() {
    const res = await fetch('/api/logs');
    const logs = await res.json();
    const container = document.getElementById('log-container');
    container.innerHTML = '';
    logs.forEach(log => {
        const p = document.createElement('div');
        p.className = 'log-entry';
        p.innerHTML = `<span class="log-time">[${log.time}]</span><span class="log-level log-${log.level}">${log.level}</span><span class="log-msg">${log.message}</span>`;
        container.appendChild(p);
    });
    container.scrollTop = container.scrollHeight;
}

function copyLogs() {
    navigator.clipboard.writeText(document.getElementById('log-container').innerText);
    showToast("Logs copied", 'success');
}

setInterval(() => { if(document.getElementById('view-logs').classList.contains('active')) loadLogs(); }, 3000);
