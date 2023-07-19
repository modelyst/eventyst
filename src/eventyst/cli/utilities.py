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

import os
import sys

import typer
from rich.traceback import Traceback

from eventyst.cli.styles import bad_typer_print, typer_print
from eventyst.core.application import Eventyst

# Errors
ERROR_FORMAT = "Application is not in MODULE:PACKAGE format: {0}"
ERROR_DEFAULT_APP = (
    "Could not find app at app.main:make_app.\nThis is the default --app value, did you forget to set --app?"
)
ERROR_MODULE = "Could not find module:\nModule: {0}\nPackage: {1}\nError: {2}"
ERROR_PACKAGE = "Could not find package within module:\nModule: {0}\nPackage: {1}\nError: {2}"
ERROR_ATTR = "Could not find Attribute within package:\nModule: {0}\nPackage: {1}\nError: {2}"
ERROR_NOT_APP = "Import String is not for a DBgen Model: \nImport String: {0}\nClass: {1}"
ERROR_NOT_APP_FUNCTION = (
    "Import String is for a function that does not produce a DBgen Model: \nImport String: {0}\nOutput Class: {1}"
)
ERROR_RUNNING_APP_FACT = (
    "Import String is for a function produced an error or required arguments: \nImport String: {0}\n"
    "Output Class: {1} \n{2}{3}"
)


def validate_app_str(app_str: str) -> Eventyst:
    """
    Validate the user input app import str checking for malformed and invalid inputs.py

    Args:
        app_str (str): CLI/config file input in MODULE:PACKAGE format

    Raises:
        typer.BadParameter: Whenever one of many checks is failed

    Returns:
        Eventyst: the output app after checks are in place
    """
    # Add current workind directory to the path at the end
    cwd = os.getcwd()
    sys.path.insert(0, cwd)

    def basic_error(fmt, val):
        return typer.BadParameter(fmt.format(*val), param_hint="--app")

    if app_str is None:
        raise typer.BadParameter("--app is required.")

    # Check for empty string app_strs
    if app_str in (":", ""):
        raise basic_error(ERROR_FORMAT, [app_str])

    split_app = app_str.split(":")
    if len(split_app) != 2:
        raise basic_error(ERROR_FORMAT, [app_str])
    module, package = split_app
    try:
        _temp = __import__(module, globals(), locals(), [package])
        app = getattr(_temp, package)
        if isinstance(app, Eventyst):
            return app
        elif callable(app):
            try:
                app = app()
            except TypeError as exc:
                print(exc)
                import traceback

                exc_str = traceback.format_exc()
                raise basic_error(
                    ERROR_RUNNING_APP_FACT, [app_str, type(app).__name__, "#" * 24 + "\n", str(exc_str)]
                ) from exc
            if isinstance(app, Eventyst):
                return app
            raise basic_error(ERROR_NOT_APP_FUNCTION, [app_str, type(app).__name__])

        raise basic_error(ERROR_NOT_APP, [app_str, type(app).__name__])
    except (ModuleNotFoundError, AttributeError) as exc:
        if app_str == 'app.main:make_app':
            raise basic_error(ERROR_DEFAULT_APP, []) from exc
        if f"No module named {module!r}" in str(exc):
            raise basic_error(ERROR_MODULE, [module, package, str(exc)]) from exc
        if isinstance(exc, AttributeError):
            typer_print('red')(Traceback(width=150))
            raise basic_error(ERROR_ATTR, [module, package, str(exc)]) from exc
        bad_typer_print(f"Error loading app at location '{module}.{package}'...")
        typer_print('red')(Traceback(width=150))
        raise typer.Exit(code=1)
    except Exception:
        bad_typer_print(f"Error loading app at location '{module}.{package}'...")
        typer_print('red')(Traceback(width=150))
        raise typer.Exit(code=1)
