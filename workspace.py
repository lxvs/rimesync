import sys
from pathlib import Path

def __workspace() -> Path:
    if getattr(sys, 'frozen', False):
        path = getattr(sys, '_MEIPASS', sys.executable)
    else:
        path = __file__
    return Path(path).resolve().parent

WORKSPACE = __workspace()
