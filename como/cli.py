# -*- coding: utf-8 -*-
"""
como.cli - command line stuff
"""

import sys

from paxo.core import Paxo
from paxo.util import is_lin, is_win, is_osx, ExitStatus
from paxo.text import error

supported = is_lin or is_osx or is_win

from como import __version__
from como.core import cmd_save

app = Paxo('como', 'a Cecil Woebker project.', '<command>',
           __version__, default_action=cmd_save)


def main():
    if not supported:
        error("Your OS is not supported.")
        sys.exit(ExitStatus.UNSUPPORTED)
    app.go()
