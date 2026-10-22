import subprocess
import re
import time
import qrcode
from ui import console

def get_ip(serial):
    result = subprocess.run(['adb', '-s', serial, 'shell', 'ip', 'route'], capture_output=True, text=True)
    match = re.search(r'src (\d+\.\d+\.\d+\.\d+)', result.stdout)
    if match: return match.group(1)
    result = subprocess.run(['adb', '-s', serial, 'shell', 'ip', 'addr', 'show', 'wlan0'], capture_output=True, text=True)
    match = re.search(r'inet (\d+\.\d+\.\d+\.\d+)', result.stdout)
    if match: return match.group(1)
    return None

def go_wireless(serial):
    console.print("[yellow]Searching for Phone IP...[/yellow]")
    ip = get_ip(serial)
    
    if not ip or ip.startswith("100."):
        if ip: console.print(f"[bold yellow]Detected IP {ip} (VPN/Mobile Data).[/bold yellow]")
        console.print("[bold cyan]Please enter the IP address from your phone's Wi-Fi settings (e.g., 192.168.1.X):[/bold cyan]")
        ip = console.input("[bold green]IP Address: [/bold green]").strip()

    console.print(f"[bold green]Using IP: {ip}:5555[/bold green]")
    console.print("[yellow]Switching phone to Wireless ADB...[/yellow]")
    subprocess.run(['adb', '-s', serial, 'tcpip', '5555'], capture_output=True)
    time.sleep(2)
    
    qr = qrcode.QRCode(version=1, box_size=1, border=1)
    qr.add_data(f"adb connect {ip}:5555")
    qr.make(fit=True)
    console.print("\n[bold cyan]Wireless Setup Ready![/bold cyan]")
    qr.print_ascii(invert=True)

    console.print(f"\n[bold yellow]IMPORTANT: UNPLUG your USB cable before launching![/bold yellow]")
    return ip, True
