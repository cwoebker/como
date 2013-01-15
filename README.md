# como: batteries complete

[`como`](https://github.com/cwoebker/como/blob/master/como.py) is a minimalistic utillity to monitor and log battery health & more.

[![Status unavailable](https://secure.travis-ci.org/cwoebker/como.png?branch=master)](http://travis-ci.org/cwoebker/como)

---

## Naming ##

**Why como?**

The answer is simple: Alessandro Volta grew up in the town of [Como](https://maps.google.com/maps/place?ftid=0x47869c481027ed63:0xb99b96af785ff524&q=Como+italy&gl=us&ie=UTF8&ll=45.905539,8.869743&spn=0.000239,0.000343&t=h&z=12&vpsrc=0)
and since he invented the battery I thought it would be a great name.

![Map not found](https://mts0.google.com/vt/data=9JDtAHjlTn3x-Sj-pwj3TI8qbtmqB_-LnEoOWHi1JIH9W7fJrfYPYf2ali6aD042Ny8SYFLwPPZZKXlfEZ4QdxIpwulW3ms6uP5wUAoVf93Jyw3RqOzuf7phyiJTNTa7F40NnNzgarXK_1t3AxD-WqBu5Go8Gincuj1Ho04og_3Sa2UiBghMZdgO5C25rkiQkreOKiiL1sBaWOqNe2jnAM4MI2IC)


## Usage

    como

Saves the current battery state.

    como info

Prints information about battery and battery history.

    como import <file>

Import statistics from .csv file (time, capacity, cycles)

    como export

Saves data to `como.csv` file to current directory.

    como upload

Uploads data to server.

    como open

Opens personal battery information page.

    como automate

Turns scheduling on or off. Saving and Uploading.

    como init

Quick command to get everything setup on first start.

    como reset

Removes all entries in database.

    como --help

Shows a complete help.

    como --version

Shows the current version.


## Installation

Installing `como` is **simple**:

    $ pip install como


## Advanced

``como`` stores all battery information (with zlib compression) in the file ``~/.como``.
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
- Upload Data to server

## Contribute

[Fork and contribute!](http://github.com/cwoebker/como)

---

Question's and suggestions, feel free to shoot me an email <me@cwoebker.com>

Follow [@cwoebker](http://twitter.com/cwoebker)

---

Copyright (c) 2012, Cecil Woebker.
License: BSD (see LICENSE for details)
