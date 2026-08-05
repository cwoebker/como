"""
como.cli - entry point
"""

import sys

import click

from como import __version__
from como.core import (
    ComoError,
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
        try:
            cmd_save()
        except (ComoError, RuntimeError) as e:
            raise click.ClickException(str(e)) from e


@main.command()
def save() -> None:
    """Save current battery state to the database."""
    try:
        cmd_save()
    except (ComoError, RuntimeError) as e:
        raise click.ClickException(str(e)) from e


@main.command()
def info() -> None:
    """Show current battery information."""
    try:
        cmd_info()
    except (ComoError, RuntimeError) as e:
        raise click.ClickException(str(e)) from e


@main.command()
@click.option(
    "--since",
    default=None,
    help="Limit to entries from the last N periods (e.g. 30d, 4w, 6m, 1y).",
)
def data(since: str | None) -> None:
    """Show database stats and history graphs."""
    try:
        cmd_data(since=since)
    except (ComoError, RuntimeError) as e:
        raise click.ClickException(str(e)) from e


@main.command()
def reset() -> None:
    """Delete the database."""
    cmd_reset()


@main.command(name="import")
@click.argument("file", type=click.Path(exists=True))
def import_data(file: str) -> None:
    """Import battery data from a CSV file."""
    try:
        cmd_import(file)
    except (ComoError, RuntimeError) as e:
        raise click.ClickException(str(e)) from e


@main.command(name="export")
def export_data() -> None:
    """Export database to como.csv in the current directory."""
    try:
        cmd_export()
    except (ComoError, RuntimeError) as e:
        raise click.ClickException(str(e)) from e


@main.command()
def automate() -> None:
    """Toggle automatic scheduling (launchd on macOS, cron on Linux)."""
    cmd_automate()
