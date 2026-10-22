from flask import Flask, render_template, request, jsonify, Response
import subprocess
import os
import time
import datetime
import re
from werkzeug.utils import secure_filename
from adb_manager import get_devices

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024
current_device = None
sys_logs = []

def add_log(level, message):
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    sys_logs.append({"time": timestamp, "level": level, "message": message})
    if len(sys_logs) > 50: sys_logs.pop(0)

def ensure_connection():
    global current_device
    if current_device and '.' in current_device:
        subprocess.run(['adb', 'connect', current_device], capture_output=True, text=True, timeout=5)

@app.route('/')
def index(): return render_template('index.html')

@app.route('/api/logs', methods=['GET'])
def get_logs(): return jsonify(sys_logs)

@app.route('/api/gallery', methods=['GET'])
def get_gallery():
    global current_device
    if not current_device: return jsonify([])
    ensure_connection()
    try:
        res = subprocess.run(['adb', '-s', current_device, 'shell', 'ls', '-t', '/sdcard/DCIM/Camera/PhantomShot_*.png'], capture_output=True, text=True, timeout=10)
        files = [f.strip() for f in res.stdout.split('\n') if f.strip().endswith('.png')]
        images = []
        for f in files:
            filename = os.path.basename(f)
            time_str = filename.replace('PhantomShot_', '').replace('.png', '')
            try: formatted_time = datetime.datetime.strptime(time_str, "%Y%m%d_%H%M%S").strftime("%Y-%m-%d %H:%M:%S")
            except: formatted_time = "Unknown Time"
            images.append({"filename": filename, "time": formatted_time})
        return jsonify(images)
    except: return jsonify([])

@app.route('/api/image/<filename>', methods=['GET'])
def serve_image(filename):
    global current_device
    if not current_device: return "No device", 404
    try:
        res = subprocess.run(['adb', '-s', current_device, 'exec-out', 'cat', f'/sdcard/DCIM/Camera/{filename}'], capture_output=True)
        if res.returncode == 0: return Response(res.stdout, mimetype='image/png')
        return "Image not found", 404
    except: return "Error", 500

@app.route('/api/delete_capture', methods=['POST'])
def delete_capture():
    global current_device
    filename = request.json.get('filename')
    if current_device:
        subprocess.run(['adb', '-s', current_device, 'shell', 'rm', f'/sdcard/DCIM/Camera/{filename}'])
        add_log("WARNING", f"Deleted {filename} from phone.")
        return jsonify({"success": True})
    return jsonify({"success": False})

@app.route('/api/detect_usb', methods=['GET'])
def detect_usb():
    global current_device
    try:
        devices = get_devices()
        if devices:
            current_device = devices[0]['serial']
            add_log("SUCCESS", f"USB Device Found: {devices[0]['model']}")
            return jsonify({"success": True, "model": devices[0]['model'], "serial": current_device})
        return jsonify({"success": False, "message": "No USB device detected."})
    except Exception as e: return jsonify({"success": False, "message": str(e)})

@app.route('/api/connect_wifi', methods=['POST'])
def connect_wifi():
    global current_device
    ip = request.json.get('ip')
    if not ip: return jsonify({"success": False})
    try:
        devices = get_devices()
        if devices:
            subprocess.run(['adb', '-s', devices[0]['serial'], 'tcpip', '5555'], capture_output=True)
            time.sleep(2)
        add_log("INFO", f"Connecting to {ip}...")
        result = subprocess.run(['adb', 'connect', f'{ip}:5555'], capture_output=True, text=True, timeout=10)
        if "connected" in result.stdout.lower() and "cannot" not in result.stdout.lower():
            current_device = f'{ip}:5555'
            add_log("SUCCESS", f"Wireless Connected: {ip}")
            return jsonify({"success": True})
        return jsonify({"success": False})
    except: return jsonify({"success": False})

@app.route('/api/disconnect', methods=['POST'])
def disconnect():
    global current_device
    subprocess.run(['taskkill', '/F', '/IM', 'scrcpy.exe'], capture_output=True)
    if current_device:
        subprocess.run(['adb', 'disconnect', current_device], capture_output=True)
        add_log("WARNING", f"Disconnected {current_device}.")
        current_device = None
    return jsonify({"success": True})

@app.route('/api/stop_mirror', methods=['POST'])
def stop_mirror():
    subprocess.run(['taskkill', '/F', '/IM', 'scrcpy.exe'], capture_output=True)
    add_log("INFO", "Mirror window closed.")
    return jsonify({"success": True})

@app.route('/api/mirror', methods=['POST'])
def mirror():
    global current_device
    if current_device:
        ensure_connection()
        audio_enabled = request.json.get('audio', False)
        add_log("INFO", f"Launching scrcpy (Audio: {audio_enabled})...")
        
        subprocess.run(['taskkill', '/F', '/IM', 'scrcpy.exe'], capture_output=True)
        time.sleep(1.5) 

        # THE FIX: scrcpy has audio ON by default. We only pass --no-audio if disabled.
        cmd = ['scrcpy', '-s', current_device, '--always-on-top']
        if not audio_enabled:
            cmd.append('--no-audio')
            
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        
        process = subprocess.Popen(cmd, startupinfo=startupinfo, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        time.sleep(1)
        if process.poll() is not None:
            err = process.stderr.read()
            add_log("ERROR", f"Scrcpy crashed: {err}")
            print(f"SCRCPY CRASH LOG: {err}")
            return jsonify({"success": False, "message": "Scrcpy crashed."})

        return jsonify({"success": True})
    return jsonify({"success": False})

@app.route('/api/screenshot', methods=['POST'])
def screenshot():
    global current_device
    if current_device:
        ensure_connection()
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"PhantomShot_{timestamp}.png"
        phone_path = f'/sdcard/DCIM/Camera/{filename}'
        try:
            subprocess.run(['adb', '-s', current_device, 'shell', 'screencap', '-p', phone_path], check=True, timeout=10)
            add_log("SUCCESS", f"Saved to phone gallery: {filename}")
            return jsonify({"success": True})
        except: return jsonify({"success": False})
    return jsonify({"success": False})

@app.route('/api/command', methods=['POST'])
def command():
    global current_device
    if current_device:
        ensure_connection()
        cmd_type = request.json.get('type')
        if cmd_type == 'reboot': subprocess.Popen(['adb', '-s', current_device, 'reboot'])
        elif cmd_type == 'screen_off': subprocess.run(['adb', '-s', current_device, 'shell', 'input', 'keyevent', '26'])
        elif cmd_type == 'vol_up': subprocess.run(['adb', '-s', current_device, 'shell', 'input', 'keyevent', '24'])
        elif cmd_type == 'vol_down': subprocess.run(['adb', '-s', current_device, 'shell', 'input', 'keyevent', '25'])
        add_log("INFO", f"Executed command: {cmd_type}")
        return jsonify({"success": True})
    return jsonify({"success": False})

@app.route('/api/upload', methods=['POST'])
def upload_file():
    global current_device
    if not current_device: return jsonify({"success": False, "message": "No device connected."})
    if 'file' not in request.files: return jsonify({"success": False, "message": "No file part."})
    file = request.files['file']
    if file.filename == '': return jsonify({"success": False, "message": "No selected file."})
    try:
        clean_name = secure_filename(file.filename)
        filename = f"Phantom_{clean_name}"
        temp_path = os.path.join('temp_uploads', filename)
        file.save(temp_path)
        add_log("INFO", f"Uploading {filename} to phone...")
        ensure_connection()
        res = subprocess.run(['adb', '-s', current_device, 'push', temp_path, '/sdcard/Download/'], capture_output=True, text=True)
        os.remove(temp_path)
        if res.returncode == 0:
            subprocess.run(['adb', '-s', current_device, 'shell', 'am', 'broadcast', '-a', 'android.intent.action.MEDIA_SCANNER_SCAN_FILE', '-d', f'file:///sdcard/Download/{filename}'], capture_output=True)
            add_log("SUCCESS", f"File {filename} pushed to Download folder.")
            return jsonify({"success": True, "message": "File pushed successfully!"})
        else:
            return jsonify({"success": False, "message": res.stderr})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route('/api/notifications', methods=['GET'])
def get_notifications():
    global current_device
    if not current_device: return jsonify([])
    ensure_connection()
    try:
        res = subprocess.run(['adb', '-s', current_device, 'shell', 'dumpsys', 'notification', '--noredact'], capture_output=True, text=True, timeout=15)
        output = res.stdout
        notifs = []
        blocks = re.findall(r'NotificationRecord\(.*?\n(.*?)(?=NotificationRecord|\Z)', output, re.DOTALL)
        for block in blocks[:20]:
            app_match = re.search(r'pkg=(.*?) ', block)
            title_match = re.search(r'android.title=(.*?)(\n|$)', block)
            text_match = re.search(r'android.text=(.*?)(\n|$)', block)
            if title_match or text_match:
                app = app_match.group(1).split('.')[-1].capitalize() if app_match else "App"
                title = title_match.group(1).replace('String (', '').replace(')', '').strip() if title_match else ""
                text = text_match.group(1).replace('String (', '').replace(')', '').strip() if text_match else ""
                if title or text: notifs.append({"app": app, "title": title, "text": text})
        add_log("INFO", f"Fetched {len(notifs)} notifications.")
        return jsonify(notifs)
    except Exception as e:
        return jsonify([])

if __name__ == '__main__':
    add_log("INFO", "PhantomMirror OS v3.0 Initialized.")
    app.run(debug=True, port=5000)
