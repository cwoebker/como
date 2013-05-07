# -*- coding: utf-8 -*-
"""
como.help - various stuff that helps
"""

import platform
from clint.textui import colored, puts


system = platform.system().lower()

is_osx = (system == 'darwin')
is_win = (system == 'windows')
is_lin = (system == 'linux')
supported = is_lin or is_osx or is_win

# www.github.com/kennethreitz/spark.py - this code is taken from kennethreitz
# python port of holman's original spark

TICKS = u'▁▂▃▅▆▇'


def spark_string(ints):
    """Returns a spark string from given iterable of ints."""
    step = ((
        max(i for i in ints if type(i) == int)) / float(len(TICKS) - 1)) or 1
    return u''.join(
        TICKS[int(round(i / step))] if type(i) == int else u'.' for i in ints)


def warning(msg):
    puts(colored.yellow(msg))


def error(msg):
    puts(colored.red(msg))
