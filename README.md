# como: batteries complete

[`como`](https://github.com/cwoebker/como/blob/master/como.py) is a minimalistic utillity to monitor and log battery health & more.

[![Status unavailable](https://secure.travis-ci.org/cwoebker/como.png?branch=master)](http://travis-ci.org/cwoebker/como)

---

## Usage

    como

Saves the current battery state.

    como stats

Prints information about battery and battery history.

    como import <file>

Import statistics from .csv file (time, capacity, cycles)

    como export

Saves data to `como.csv` file to current directory.

    como auto

Turns scheduling on or off. (Every day at 8am, 2pm and 8pm)

    como reset

Removes all entries in database.

    como --help

Shows a complete help.

    como --version

Shows the current version.


## Installation

Installing como is **simple**:

    $ pip install como


## Advanced

``como`` stores all battery information in the file ``~/.como``.
You are free to do whatever you want with the data in that file,
its yours after all.

So go out there and hack some code!

## Features ##

- Cross-Platform (Linux & Mac)
- Automatically run with `cron`/`launchd` scheduling
- Export data to `.csv` file
- Import data from `.csv` file
- Simple Statistics
- Histories for Cycles and Capacity

## Contribute

Fork and contribute!

---

Question's and suggestions, feel free to shoot me an email <me@cwoebker.com>

Follow [@cwoebker](http://twitter.com/cwoebker)

---

Copyright (c) 2012, Cecil Woebker.
License: BSD (see LICENSE for details)
