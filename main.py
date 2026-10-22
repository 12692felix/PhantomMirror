import sys
import os

# Force terminal to handle Unicode block characters properly
if sys.platform == 'win32':
    os.system('chcp 65001 > nul')
    sys.stdout.reconfigure(encoding='utf-8')

import subprocess
from ui import print_banner, console
from adb_manager import get_devices, launch_mirror
from wireless import go_wireless
from rich.panel import Panel

def interactive_menu(serial):
    console.print("\n[bold cyan]PhantomMirror Interactive Shell[/bold cyan]")
    console.print("Type [green]help[/green] to see available commands, or [red]exit[/red] to quit.")
    
    while True:
        try:
            cmd = console.input("[bold green]root@axtarget:~$ [/bold green]").strip().lower()
        except KeyboardInterrupt:
            console.print("\n[yellow]Exiting...[/yellow]")
            break

        if cmd == 'exit':
            console.print("[yellow]Goodbye![/yellow]")
            break
        elif cmd == 'help':
            console.print("  [cyan]screenshot[/cyan] - Saves a PNG of your phone screen")
            console.print("  [cyan]apps[/cyan]       - Lists installed 3rd-party apps")
            console.print("  [cyan]mirror[/cyan]     - Launches the screen mirror")
            console.print("  [cyan]disconnect[/cyan] - Drops the wireless connection")
            console.print("  [cyan]exit[/cyan]       - Closes this menu")
        elif cmd == 'screenshot':
            console.print("[yellow]Capturing screen...[/yellow]")
            with open('screenshot.png', 'wb') as f:
                result = subprocess.run(['adb', '-s', serial, 'exec-out', 'screencap', '-p'], stdout=f, stderr=subprocess.PIPE, text=True)
            if result.returncode == 0:
                console.print("[green]✅ Saved as screenshot.png in your project folder![/green]")
            else:
                console.print(f"[bold red]Failed to capture:[/bold red] {result.stderr.strip()}")
                f.close()
                if os.path.exists('screenshot.png'): os.remove('screenshot.png')
        elif cmd == 'apps':
            console.print("[yellow]Fetching installed apps...[/yellow]")
            result = subprocess.run(['adb', '-s', serial, 'shell', 'pm', 'list', 'packages', '-3'], capture_output=True, text=True)
            if result.returncode == 0:
                apps = result.stdout.replace('package:', '').strip().split('\n')
                for app in apps[:15]:
                    console.print(f"  - {app}")
                if len(apps) > 15:
                    console.print(f"  [dim]...and {len(apps)-15} more.[/dim]")
            else:
                console.print("[bold red]Failed to get apps.[/bold red]")
        elif cmd == 'mirror':
            console.print("[yellow]Launching scrcpy...[/yellow]")
            subprocess.run(['scrcpy', '-s', serial])
        elif cmd == 'disconnect':
            console.print("[yellow]Disconnecting wireless ADB...[/yellow]")
            subprocess.run(['adb', 'disconnect', serial], capture_output=True)
            console.print("[green]Disconnected.[/green]")
            break
        else:
            console.print("[red]Unknown command. Type 'help' for options.[/red]")

def main():
    print_banner()
    console.print("[bold green]AxtarGet System started...[/bold green]")
    
    devices = get_devices()
    
    if not devices:
        console.print(Panel("[bold red]No devices found![/bold red]\nPlease connect your Android phone via USB.", title="Device Detector"))
        sys.exit(1)
        
    serial = devices[0]['serial']
    console.print(f"[bold cyan]Device Detected:[/bold cyan] {devices[0]['model']} ({serial})")
    
    if '.' in serial:
        console.print("[bold green]Already connected wirelessly! Skipping USB setup.[/bold green]")
        interactive_menu(serial)
        return

    console.print("")
    choice = console.input("[bold yellow]Do you want to enable Wireless Mode (QR Code)? (y/n): [/bold yellow]")
    
    if choice.lower() == 'y':
        ip, success = go_wireless(serial)
        if success:
            console.input("\n[bold cyan]Press ENTER once you have UNPLUGGED the USB cable...[/bold cyan]")
            console.print(f"[dim]Connecting to {ip}...[/dim]")
            
            connect_res = subprocess.run(['adb', 'connect', f'{ip}:5555'], capture_output=True, text=True)
            if "connected" in connect_res.stdout.lower():
                console.print("[green]Connection successful![/green]")
                interactive_menu(f'{ip}:5555')
            else:
                console.print(f"[bold red]Failed to connect! Check your IP address.[/bold red]")
    else:
        interactive_menu(serial)

if __name__ == "__main__":
    main()
