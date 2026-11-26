import os
from pathlib import Path

# Kontener w agent-dashboard ma folder z kodem tylko do odczytu, więc wtedy dane idą do /tmp (znikają przy restarcie).
DATA_DIR = Path(os.environ.get("DATA_DIR") or ("." if os.access(".", os.W_OK) else "/tmp/giga-china-crawler"))
DATA_DIR.mkdir(parents=True, exist_ok=True)
