# coco: batteries complete

[`coco.py`](https://github.com/cwoebker/coco/blob/master/coco.py) is a minimalistic utillity to monitor and log battery health & more.

[![Status unavailable](https://secure.travis-ci.org/cwoebker/coco.png?branch=master)](http://travis-ci.org/cwoebker/coco)

---

## Usage

    coco

Saves the current battery state.

    coco stats

Prints information about battery and battery history.

    coco save

Saves data to `coco.csv` file to current directory.

    coco auto

Turns scheduling on or off. (Every day at 18:30)

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
