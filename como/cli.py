# -*- coding: utf-8 -*-
"""
como.cli - command line stuff
"""

import sys


from paxo import Paxo
from paxo.command import define_command

from como import __version__
from como.help import supported, error, args
from como.core import cmd_save, cmd_reset, cmd_data, cmd_info, cmd_import, cmd_export, \
    cmd_upload, cmd_open, auto_save, auto_upload

app = Paxo('como', 'A Cecil Woebker Project.', '<command>',
           __version__, default_action=cmd_save)


def main():
    if not supported:
        error("Your OS is not supported.")
        sys.exit(1)
    app.go()


def cmd_init(args):
    cmd_save(args)
    cmd_automate(args)
    cmd_save(args)  # double save so user sees actual graph on site
    cmd_upload(args)
    cmd_open(args)


def cmd_automate(args):
    auto_save()
    auto_upload()

define_command(
    name='init', fn=cmd_init, usage='init',
    help='Initializes como.')

define_command(
    name='automate', fn=cmd_automate, usage='automate',
    help='Automates saving and uploading.')

define_command(
    name='save', fn=cmd_save, usage='save',
    help='Saves battery information to database.')

define_command(
    name='reset', fn=cmd_reset, usage='reset',
    help='Deletes database.')

define_command(
    name='data', fn=cmd_data, usage='data',
    help='Shows database information.')

define_command(
    name='info', fn=cmd_info, usage='info',
    help='Shows battery information.')

define_command(
    name='import', fn=cmd_import, usage='import <file>',
    help='Import data from .csv file.')

define_command(
    name='export', fn=cmd_export, usage='export',
    help='Export data to .csv file.')

define_command(
    name='upload', fn=cmd_upload, usage='upload',
    help='Upload data to server.')

define_command(
    name='open', fn=cmd_open, usage='open',
    help='Open your battery page.')
