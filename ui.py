from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from pyfiglet import Figlet

console = Console()

def print_banner():
    f = Figlet(font='slant')
    ascii_art = f.renderText('PhantomMirror')
    console.print(f"[bold green]{ascii_art}[/bold green]")
    console.print("[dim green]Advanced Android Screen Mirroring & Controller v1.0[/dim green]\n")

def prompt(text):
    return console.input(f"[bold green]root@axtarget:~$ [/bold green]")
