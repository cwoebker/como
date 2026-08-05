"""
como.cli - entry point
"""

import sys

import click

from como import __version__
from como.core import (
    cmd_automate,
    cmd_data,
    cmd_export,
    cmd_import,
    cmd_info,
    cmd_reset,
    cmd_save,
)

_SUPPORTED = sys.platform in ("darwin", "linux", "win32")


@click.group(invoke_without_command=True)
@click.version_option(__version__, prog_name="como")
@click.pass_context
def main(ctx: click.Context) -> None:
    """como — battery history tracker."""
    if not _SUPPORTED:
        click.echo(f"Unsupported platform: {sys.platform}", err=True)
        sys.exit(1)
    if ctx.invoked_subcommand is None:
        cmd_save()


@main.command()
def save() -> None:
    """Save current battery state to the database."""
    cmd_save()


@main.command()
def info() -> None:
    """Show current battery information."""
    cmd_info()


@main.command()
def data() -> None:
    """Show database stats and history graphs."""
    cmd_data()


@main.command()
def reset() -> None:
    """Delete the database."""
    cmd_reset()


@main.command(name="import")
@click.argument("file", type=click.Path(exists=True))
def import_data(file: str) -> None:
    """Import battery data from a CSV file."""
    cmd_import(file)


@main.command(name="export")
def export_data() -> None:
    """Export database to como.csv in the current directory."""
    cmd_export()


@main.command()
def automate() -> None:
    """Toggle automatic scheduling (launchd on macOS, cron on Linux)."""
    cmd_automate()
