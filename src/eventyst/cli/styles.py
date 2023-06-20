#   Copyright 2022 Modelyst LLC
#   All Rights Reserved

"""Utilities for printing things to screen for CLI."""
import typer
from rich.console import Console, Group
from rich.panel import Panel
from rich.text import Text
from rich.theme import Theme

from eventyst import __version__

THEME_COLOR = typer.colors.GREEN
theme = Theme({'theme': 'magenta'})
console = Console(theme=theme)
LOGO = """
███████╗██╗   ██╗███████╗███╗   ██╗████████╗██╗   ██╗███████╗████████╗
██╔════╝██║   ██║██╔════╝████╗  ██║╚══██╔══╝╚██╗ ██╔╝██╔════╝╚══██╔══╝
█████╗  ██║   ██║█████╗  ██╔██╗ ██║   ██║    ╚████╔╝ ███████╗   ██║
██╔══╝  ╚██╗ ██╔╝██╔══╝  ██║╚██╗██║   ██║     ╚██╔╝  ╚════██║   ██║
███████╗ ╚████╔╝ ███████╗██║ ╚████║   ██║      ██║   ███████║   ██║
╚══════╝  ╚═══╝  ╚══════╝╚═╝  ╚═══╝   ╚═╝      ╚═╝   ╚══════╝   ╚═╝"""

VERSION = f"""VERSION: {__version__}"""


def delimiter(color: str = THEME_COLOR):
    console.rule(style=color)


LOGO_STYLE = Panel.fit(
    Group(Panel(Text(LOGO)), Panel(Text(VERSION, justify='center'))),
    style='theme',
)


# Easy printers
def typer_print(color=None):
    return lambda msg: console.print(msg, style=color)


good_typer_print = typer_print('green')
bad_typer_print = typer_print('red')
theme_typer_print = typer_print('theme')
