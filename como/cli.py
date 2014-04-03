# -*- coding: utf-8 -*-
"""
como.cli - command line stuff
"""

import sys

from clint.textui import colored, puts

from .core import ExitStatus
from como import __version__
from como.help import supported, error, args
from como.core import cmd_save, cmd_reset, cmd_data, cmd_info, cmd_import, cmd_export, \
    cmd_upload, cmd_open, auto_save, auto_upload


def main():
    if not supported:
        error("Your OS is not supported.")
        sys.exit(1)
    arg = args.get(0)
    if arg:
        command = Command.lookup(arg)
        if command:
            execute(command)
            return ExitStatus.OK
        elif args.contains(('-h', '--help')):
            display_info()
            return ExitStatus.OK
        elif args.contains(('-v', '--version')):
            puts('{0} v{1}'.format(
                colored.yellow('como'),
                __version__
            ))
        else:
            error('Unknown command: {0}'.format(arg))
            display_info()
            return ExitStatus.ERROR
    else:
        execute(Command.lookup('save'))
        return ExitStatus.OK


def execute(command):
    arg = args.get(0)
    args.remove(arg)
    command.__call__(args)


def display_info():
    puts('{0}. {1}'.format(
        colored.yellow('como'), 'A Cecil Woebker Project.'))

    puts('Usage: {0} {1}'.format(
        colored.yellow('como'), colored.green('<command>')))
    puts('---------------------')
    for command in Command.all_commands():
        usage = command.usage or command.name
        help = command.help or ''
        puts('{0:40} {1}'.format(
            colored.green(usage),
            help))


def cmd_init(args):
    cmd_save(args)
    cmd_automate(args)
    cmd_save(args)  # double save so user sees actual graph on site
    cmd_upload(args)
    cmd_open(args)


def cmd_automate(args):
    auto_save()
    auto_upload()


def cmd_help(args):
    command = args.get(0)
    if command is None:
        command = 'help'
    if not Command.lookup(command):
        command = 'help'
        error('Unknown command: {0}'.format(args.get(0)))
    cmd = Command.lookup(command)
    usage = cmd.usage or ''
    help = cmd.help or ''
    help_text = '%s\n\n%s' % (usage, help)
    puts(help_text)


### Commands
class Command(object):
    COMMANDS = {}
    SHORT_MAP = {}

    @classmethod
    def register(klass, command):
        klass.COMMANDS[command.name] = command
        if command.short:
            for short in command.short:
                klass.SHORT_MAP[short] = command

    @classmethod
    def lookup(klass, name):
        if name in klass.SHORT_MAP:
            return klass.SHORT_MAP[name]
        if name in klass.COMMANDS:
            return klass.COMMANDS[name]
        else:
            return None

    @classmethod
    def all_commands(klass):
        return sorted(list(klass.COMMANDS.values()),
                      key=lambda cmd: cmd.name)

    def __init__(self, name=None, short=None, fn=None, usage=None, help=None):
        self.name = name
        self.short = short
        self.fn = fn
        self.usage = usage
        self.help = help

    def __call__(self, *args, **kw_args):
        return self.fn(*args, **kw_args)


def define_command(name=None, short=None, fn=None, usage=None, help=None):
    command = Command(name=name, short=short, fn=fn, usage=usage, help=help)
    Command.register(command)

define_command(
    name='init', fn=cmd_init, usage='init',
    help='Initializes como.')

define_command(
    name='automate', fn=cmd_automate, usage='automate',
    help='Automates saving and uploading.')

define_command(
    name='help', short=['h'], fn=cmd_help, usage='help <command>',
    help='Display help for a command.')

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
