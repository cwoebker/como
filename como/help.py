# -*- coding: utf-8 -*-
"""
como.help - various stuff that helps
"""

import platform
from clint.textui import colored, puts, indent
from clint import arguments

args = arguments.Args()

system = platform.system().lower()

is_osx = (system == 'darwin')
is_win = (system == 'windows')
is_lin = (system == 'linux')
supported = is_lin or is_osx or is_win

# www.github.com/kennethreitz/spark.py - this code is taken from kennethreitz
# python port of holman's original spark
# slightly altered

TICKS = u'▁▂▃▅▆▇'


def spark_string(ints):
    """Returns a spark string from given iterable of ints."""
    ints = [i for i in ints if type(i) == int]
    if len(ints) == 0:
        return ""
    step = (max(ints) / float(len(TICKS) - 1)) or 1
    return u''.join(
        TICKS[int(round(i / step))] if type(i) == int else u'.' for i in ints)


def title(msg):
    if not is_win:
        msg = colored.green(msg)
    with indent(4):
        puts(msg)
    puts("-" * (8 + len(msg)))


def msg(msg):
    puts(msg)


def info(msg):
    if not is_win:
        msg = colored.white(msg)
    puts(msg)


def warning(msg):
    if not is_win:
        msg = colored.yellow(msg)
    puts(msg)


def error(msg):
    if not is_win:
        msg = colored.error(msg)
    puts(msg)
