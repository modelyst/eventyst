#   Copyright 2023 Modelyst LLC
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import webbrowser
from pathlib import Path
from typing import Optional

import typer

from eventyst import __version__
from eventyst._exceptions import BrokerConnectionError
from eventyst.cli import styles
from eventyst.cli.utilities import validate_app_str
from eventyst.configuration import settings
from eventyst.utilities.plotting import draw_graph_pyvis, generate_graph

app = typer.Typer(no_args_is_help=True)


app_str_option = typer.Option(None, '--app', envvar='EVENYTST_APP_STR', help="The application to draw")


@app.command(name="version")
def version(short: bool = typer.Option(False, "-s", help="Print the raw version with no ascii art.")):
    """Display gcld version info"""
    if short:
        styles.console.print(__version__)
    else:
        styles.console.print(styles.LOGO_STYLE)


@app.command(name="config")
def get_config(
    show_password: bool = False,
    show_defaults: bool = False,
    out_pth: Optional[Path] = typer.Option(
        None,
        "--out",
        "-o",
        help="Location to write parametrized config",
    ),
):
    """
    Prints out the configuration of gcld
    """
    # If out_pth provided write the current config to the path provided and return
    if out_pth:
        with open(out_pth, "w") as f:
            f.write(settings.display(True, True))

    styles.theme_typer_print(settings.display(show_defaults, show_password))


@app.command(name="run")
def run(
    app_str: str = app_str_option,
    offset_reset: str = typer.Option('latest', help="Offset reset for consumer"),
):
    """
    Run a Eventyst application
    """
    app_str = app_str or settings.APP_STR
    app = validate_app_str(app_str)
    try:
        app.start(offset_reset)
    except BrokerConnectionError as e:
        app.logger.error(f"Could not connect to broker: {e}")
        raise typer.Exit(1)
    except KeyboardInterrupt:
        print("\r  ")
        app.logger.info("Attempting to gracefully shutdown...")
        raise typer.Exit(0)
    except Exception as e:
        app.logger.exception(f"An error occurred when starting the application: {e}", exc_info=e)
        raise typer.Exit(1)


@app.command(name="draw")
def draw(
    app_str: str = app_str_option,
    out_pth: Optional[Path] = typer.Option('example.html', "--out", "-o", help="Location to write html file"),
    buttons: list[str] = typer.Option(None, "--buttons", "-b", help="Buttons to show in the graph"),
    all_buttons: bool = typer.Option(False, "--all-buttons", "-A", help="Show all buttons in the graph"),
    auto_open: bool = typer.Option(False, "--open", "-O", help="Open the graph in a browser"),
):
    """
    Draw the application
    """
    app_str = app_str or settings.APP_STR
    app = validate_app_str(app_str)

    G = generate_graph(app.registry)
    net = draw_graph_pyvis(G)
    # open in browser
    if all_buttons:
        net.show_buttons()
    elif buttons:
        net.show_buttons(filter_=buttons)

    net.show(str(out_pth))
    if auto_open:
        webbrowser.open(str(out_pth))
