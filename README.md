# 🟢 PHANTOM_MIRROR OS v3.0

A premium, full-stack Android device-control and screen-mirroring workstation. Built with Python (Flask) and a custom dark-mode JavaScript frontend, this tool wraps `scrcpy` and `adb` into a beautiful, easy-to-use desktop web interface.

<!-- Replace this with a real screenshot later! -->
![PhantomMirror UI](https://via.placeholder.com/1000x500/0B0F14/22D3EE?text=PhantomMirror+OS+v3.0)

## 🚀 Features
*   **Live Screen Mirroring** (Native pop-up window powered by `scrcpy`)
*   **Wireless Audio Forwarding** (Stream phone audio to PC speakers)
*   **File Transfer Wizard** (Drag & drop files directly to phone storage)
*   **Notification Reader** (Parses real-time Android notifications)
*   **Wireless ADB Uplink** (Connect via Wi-Fi and unplug the USB)
*   **Screenshot Gallery** (Capture and view phone screen directly in the browser)

## 🛠️ Tech Stack
*   **Backend:** Python, Flask, ADB (Android Debug Bridge), Scrcpy
*   **Frontend:** HTML5, CSS3 (Custom Dark Theme), Vanilla JavaScript, Lucide Icons
*   **Tools:** `subprocess` for system-level orchestration

## 💻 Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/12692felix/PhantomMirror.git
   cd PhantomMirror