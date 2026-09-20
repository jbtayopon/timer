import json
import os
from pathlib import Path


def get_data_folder():
    folder = Path(os.environ.get("PUBLIC", Path.home())) / "Documents" / "TPX"
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def save_events(events):
    path = get_data_folder() / "events.json"

    with open(path, "w", encoding="utf-8") as f:
        json.dump(events, f, indent=4, ensure_ascii=False)


def load_events():
    path = get_data_folder() / "events.json"

    if not path.exists():
        return []

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []