# como — track battery health from the command line

[![PyPI Version](https://img.shields.io/pypi/v/como.svg)](https://pypi.python.org/pypi/como)
[![PyPI Python Versions](https://img.shields.io/pypi/pyversions/como.svg)](https://pypi.python.org/pypi/como)
[![PyPI License](https://img.shields.io/pypi/l/como.svg)](https://pypi.python.org/pypi/como)

`como` is a minimal CLI for recording and inspecting your laptop battery's health over time. It runs on macOS and Linux, stores everything locally in SQLite, and can schedule itself via `launchd` or `cron`.

## Naming

Alessandro Volta — who invented the battery — grew up in [Como](https://maps.google.com/maps/place?ftid=0x47869c481027ed63:0xb99b96af785ff524&q=Como+italy&gl=us&ie=UTF8&ll=45.905539,8.869743&spn=0.000239,0.000343&t=h&z=12&vpsrc=0), Italy. The name stuck.

![Map of Como, Italy](https://mts0.google.com/vt/data=9JDtAHjlTn3x-Sj-pwj3TI8qbtmqB_-LnEoOWHi1JIH9W7fJrfYPYf2ali6aD042Ny8SYFLwPPZZKXlfEZ4QdxIpwulW3ms6uP5wUAoVf93Jyw3RqOzuf7phyiJTNTa7F40NnNzgarXK_1t3AxD-WqBu5Go8Gincuj1Ho04og_3Sa2UiBghMZdgO5C25rkiQkreOKiiL1sBaWOqNe2jnAM4MI2IC)

## Install

```bash
uv tool install como     # recommended
pipx install como        # alternative
pip install como         # also fine
```

## Usage

| Command | Description |
| --- | --- |
| `como` / `como save` | Record the current battery snapshot |
| `como info` | Show current battery details (capacity, cycles, voltage, power, health) |
| `como data [--since 30d]` | Show database stats and capacity/cycle history graphs. `--since` accepts `d`/`w`/`m`/`y` (e.g. `30d`, `4w`, `6m`, `1y`) |
| `como export` | Write `como.csv` to the current directory |
| `como import <file.csv>` | Import battery records from a CSV file |
| `como automate` | Toggle scheduled saves (`launchd` on macOS, `cron` on Linux) at 8:00, 14:00, 20:00 |
| `como reset` | Delete the local database |

## Storage

Battery records live in a single SQLite database at:

- macOS / Linux: `$XDG_DATA_HOME/como/como.db` (defaults to `~/.local/share/como/como.db`)
- Windows: `%APPDATA%\como\como.db`

The schema captures `time`, `capacity`, `cycles`, `voltage_mv`, `power_mw`, and `is_charging` for every save. Old zlib-compressed JSON databases from previous versions are migrated transparently on first run (a `.bak` of the original is kept alongside).

## Development

Requires [mise](https://mise.jdx.dev) and [uv](https://docs.astral.sh/uv/).

```bash
mise install              # installs Python + uv per mise.toml
uv sync                   # creates .venv with all deps
uv run como info          # run the working-tree CLI (no install needed)
uv run pytest             # run tests with coverage
uv run pre-commit install # enable ruff + ty pre-commit hooks
```

## Releasing

Releases are automated via GitHub Actions:

1. Run the **Bump version** workflow (`Actions` → `Bump version` → `Run workflow`, choose `patch`/`minor`/`major`). It bumps `pyproject.toml`/`uv.lock`, commits, tags (`vX.Y.Z`), and triggers the release workflow.
2. The **Release** workflow (`.github/workflows/release.yml`) then builds the sdist/wheel, runs the test suite, publishes to PyPI, and creates a GitHub Release with the built artifacts attached and notes drawn from `HISTORY.md` (falling back to GitHub's auto-generated notes).

Pushing a `v*.*.*` tag directly also triggers the release workflow, so a manual `git tag vX.Y.Z && git push origin vX.Y.Z` works too.

Publishing to PyPI uses [Trusted Publishing](https://docs.pypi.org/trusted-publishers/) (OIDC) — no API token is stored in the repo. This requires a one-time setup on PyPI: on the [`como` project's](https://pypi.org/manage/project/como/publishing/) publishing settings, add a trusted publisher for this repository, workflow `release.yml`, and environment `pypi`.

## License

MIT — see [LICENSE](LICENSE).

Copyright (c) 2012-2026, Cecil Wöbker. Contact: <me@cwoebker.com>.
