# -*- coding: utf-8 -*-
"""
como.settings - some global variables
"""

import os

from como.help import args

LOCATION_CODES = [
    '1C', '2Z', '4H', '5K', '8H', '5D', '7J', 'CK', 'E', 'EE',
    'F', 'FC', 'G8', 'GQ', 'PT', 'CY', 'QT', 'QP', 'RN', 'RM',
    'SG', 'UV', 'U2', 'V7', 'VM', 'W8', 'WQ', 'XA', 'XB', 'YM'
]

DEV_URL = 'http://127.0.0.1:5000'
REAL_URL = 'http://como.cwoebker.com'
COMO_BATTERY_FILE = os.path.expanduser('~/.como')

if args.contains(('-d', '--dev')):
    SERVER_URL = DEV_URL
else:
    SERVER_URL = REAL_URL
