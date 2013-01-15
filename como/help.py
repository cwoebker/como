# -*- coding: utf-8 -*-
"""
como.help - various stuff that helps
"""

import platform

from clint.textui import puts

system = platform.system().lower()

is_osx = (system == 'darwin')
is_win = (system == 'windows')
is_lin = (system == 'linux')


def first_sentence(s):
    pos = s.find('. ')
    if pos < 0:
        pos = len(s) - 1
    return s[:pos + 1]

# www.github.com/kennethreitz/spark.py - this code is taken from kennethreitz
# python port of holman's original spark

TICKS = u'▁▂▃▅▆▇'


def spark_string(ints):
    """Returns a spark string from given iterable of ints."""
    step = ((
        max(i for i in ints if type(i) == int)) / float(len(TICKS) - 1)) or 1
    return u''.join(
        TICKS[int(round(i / step))] if type(i) == int else '.' for i in ints)


def spark_print(ints):
    """Prints spark to given stream."""
    puts(spark_string(ints).encode('utf-8'))
