# coco: batteries complete

[`coco`](https://github.com/cwoebker/coco/blob/master/coco.py) is a minimalistic utillity to monitor and log battery health & more.

[![Status unavailable](https://secure.travis-ci.org/cwoebker/coco.png?branch=master)](http://travis-ci.org/cwoebker/coco)

---

## Usage

    coco

Saves the current battery state.

    coco stats

Prints information about battery and battery history.

    coco import <file>

Import statistics from .csv file (time, capacity, cycles)

    coco export

Saves data to `coco.csv` file to current directory.

    coco auto

Turns scheduling on or off. (Every day at 8am, 2pm and 8pm)

    coco reset

Removes all entries in database.

    coco --help

Shows a complete help.

    coco --version

Shows the current version.


## Installation

Installing coco is **simple**:

    $ pip install coco


## Advanced

``coco`` stores all battery information in the file ``~/.coco``.
You are free to do whatever you want with the data in that file,
its yours after all.

So go out there and hack some code!

## Features ##

- Cross-Platform (Linux & Mac)
- Automatically run with `cron`/`launchd` scheduling
- Export the data to `.csv` file
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
