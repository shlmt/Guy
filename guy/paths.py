from pathlib import Path

GUY_HOME = Path.home() / ".guy"
CONFIG_FILE = GUY_HOME / "config.json"

WORK_DIR = Path.cwd()
GUY_DIR = WORK_DIR / ".guy"
GUY_DIR.mkdir(parents=True, exist_ok=True)

SESSION_DIR = GUY_DIR / "sessions"
SESSION_DIR.mkdir(parents=True, exist_ok=True)
