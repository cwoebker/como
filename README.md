# como: batteries complete

[`como`](https://github.com/cwoebker/como) is a minimalistic utillity to monitor your battery.

[![PyPI Version](https://img.shields.io/pypi/v/penpal.svg)](https://pypi.python.org/pypi/como)
[![Build Status](https://secure.travis-ci.org/cwoebker/como.png?branch=master)](http://travis-ci.org/cwoebker/como)
[![PyPI License](https://img.shields.io/pypi/l/como.svg)](https://pypi.python.org/pypi/como)
[![PyPI Python Versions](https://img.shields.io/pypi/pyversions/como.svg)](https://pypi.python.org/pypi/como)
[![Say Thanks!](https://img.shields.io/badge/Say%20Thanks-!-1EAEDB.svg)](https://saythanks.io/to/cwoebker)

---

## Naming ##

**Why como?**

The answer is simple: Alessandro Volta grew up in the town of [Como](https://maps.google.com/maps/place?ftid=0x47869c481027ed63:0xb99b96af785ff524&q=Como+italy&gl=us&ie=UTF8&ll=45.905539,8.869743&spn=0.000239,0.000343&t=h&z=12&vpsrc=0)
and since he invented the battery I thought it would be a great name.

![Map not found](https://mts0.google.com/vt/data=9JDtAHjlTn3x-Sj-pwj3TI8qbtmqB_-LnEoOWHi1JIH9W7fJrfYPYf2ali6aD042Ny8SYFLwPPZZKXlfEZ4QdxIpwulW3ms6uP5wUAoVf93Jyw3RqOzuf7phyiJTNTa7F40NnNzgarXK_1t3AxD-WqBu5Go8Gincuj1Ho04og_3Sa2UiBghMZdgO5C25rkiQkreOKiiL1sBaWOqNe2jnAM4MI2IC)

## What is this? ##

With como you can check out how your battery is doing.
You can easily `automate` this process so that you don't need to worry about it. 
Every once in a while you can quickly check out your battery `info`.
You can `export` this data into the portable `.csv` format and `import` it again later.
You can even import data form another battery utility such as [coconutBattery](http://www.coconut-flavour.com).

## [como.cwoebker.com](https://como.cwoebker.com) ##

Most importantly you can take all this to the next level, if you choose to do so.
`Upload` your battery data to the como web application to check everything out in a nice interface wherever you are. 
You can always easily `open` your computer's personal page.

## Installation

It's as simple as that:

`$ pip install como`

Afterwards run the `init` command to get everything setup and stop worrying.

`$ como init`

## Usage

`como` - Saves the current battery state.

`como info` - Prints information about battery and battery history.

`como import <file>` - Imports statistics from .csv file (time, capacity, cycles)

`como export` - Exports data to `como.csv` file to current directory.

`como upload` - Uploads data to server.

`como open` - Opens personal battery information page.

`como automate` - Turns scheduling on or off. Saving and Uploading.

`como init` - Quick command to get everything setup on first start.

`como reset` - Removes all entries in database.


## Advanced

`como` stores all battery information (with zlib compression) in the file `~/.como`.
You are free to do whatever you want with this data, it is yours after all.

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

[Fork and contribute!](https://github.com/cwoebker/como)

---

For questions and suggestions, feel free to shoot me an email at <me@cwoebker.com>.

Also, follow or tweet [@cwoebker](https://twitter.com/cwoebker).

---

Copyright (c) 2012-2018, Cecil Wöbker.
License: BSD (see LICENSE for details)
