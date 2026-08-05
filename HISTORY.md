# History #

## 0.8.0 ##

*June 2nd 2026*

- Modernize packaging: `pyproject.toml` + `uv` (Python >=3.10), drop `setup.py`/`Pipfile`
- Rewrite CLI on `click` + `rich`; remove `paxo`/`clint`
- Rewrite battery collection per platform:
    - macOS: `ioreg` + `plistlib` (works on Apple Silicon)
    - Linux: `/sys/class/power_supply/` (replaces removed `/proc/acpi/battery/`)
    - Windows: PowerShell CIM queries, no extra deps
- Add multi-battery support and capture voltage, power, and charging state
- `como data --since 30d|4w|6m|1y` to filter history
- Switch storage to SQLite at `$XDG_DATA_HOME/como/como.db` (transparent migration from the old zlib-JSON `~/.como`, with `.bak`)
- Remove `upload`/`open`/`init` (`como.cwoebker.com` is gone)
- Proper non-zero exit codes via `ComoError` -> `click.ClickException`
- License switched from BSD to MIT
- Tooling: ruff (lint + format), ty (type check), pytest with coverage, pre-commit, Dependabot, `mise.toml`

## 0.7.0 ##

*September 27th 2020*

- Migrate to Python 3
- Update to `paxo` 0.3.0

## 0.6.2 ##

*October 9th 2018*

- Add support for MacOS Mojave

## 0.6.1 ##

*August 28th 2018*

- Using XDG_DATA_HOME for como data file
- Quick fix so that como works with current Mac computers

## 0.6.0 ##

*March 23rd 2015*

- Using the "paxo" command line library

## 0.5.1 ##

*February 9th 2015*

- Fixed an issue where como wouldn't work due to the new Mac serial format

## 0.5.0 ##

*January 16th 2013*

- improved code structure
- finalized basic code api for 0.5.0 release

## 0.4.7 ##

*January 14th 2013*

- restructured everything into multiple files
- replaced docopt with clint
- added init command for quick initial setup

## 0.4.6 ##

*January 12th 2013*

- fixed auto uploading
- improved code for pep8 guidelines
- (-d) or (--dev) option to use local development server

## 0.4.5 ##

*January 10th 2013*

- data is now stored with zlib compression
- upload to web app - **BETA**
    - check on battery (como.cwoebker.com)
    - see health status and more

## 0.4.0 ##

*January 5th 2013*

- Rewrote the code to consistently use tablib
- Added `import` features
- Added more info to `stats`
- Auto scheduling 3 times a day (8am, 2pm and 8pm)
- Other minor fixes

## 0.3.1 ##

*December 16th 2012*

- Quick fix for scheduling, more reliable now

## 0.3.0 ##

*December 11th 2012*

- Added automatic scheduling
- Simplified much code
- Added some Linux functionality **Not tested**