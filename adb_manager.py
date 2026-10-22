import subprocess
import sys
from ui import console

def get_devices():
    """Runs 'adb devices' and parses the output."""
    try:
        result = subprocess.run(['adb', 'devices'], capture_output=True, text=True, check=True)
        lines = result.stdout.strip().split('\n')[1:]
        devices = []
        
        for line in lines:
            if line.strip() and 'device' in line and 'offline' not in line:
                parts = line.split('\t')
                serial = parts[0]
                # Get the model name
                model_result = subprocess.run(['adb', '-s', serial, 'shell', 'getprop', 'ro.product.model'], capture_output=True, text=True)
                model = model_result.stdout.strip()
                devices.append({'serial': serial, 'model': model})
                
        return devices
    except FileNotFoundError:
        console.print("[bold red]Error: adb is not installed or not in your PATH.[/bold red]")
        sys.exit(1)

def launch_mirror(serial):
    console.print(f"[bold green]Starting scrcpy for device {serial}...[/bold green]")
    try:
        subprocess.run(['scrcpy', '-s', serial])
    except FileNotFoundError:
        console.print("[bold red]Error: scrcpy is not installed or not in your PATH.[/bold red]")
