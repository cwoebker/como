import os
import sys
from pathlib import Path

if sys.platform == "win32":
    _data_home = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
else:
    _data_home = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))

COMO_BATTERY_FILE = _data_home / "como" / "como"
