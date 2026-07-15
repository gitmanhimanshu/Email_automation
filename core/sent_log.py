"""A running record of every email this tool has sent."""
import json
from datetime import datetime

from . import config


def read(limit=None):
    if not config.SENT_LOG_PATH.exists():
        return []
    try:
        entries = json.loads(config.SENT_LOG_PATH.read_text())
    except json.JSONDecodeError:
        return []
    if not isinstance(entries, list):
        return []
    return entries[-limit:] if limit else entries


def record(results):
    """Append results to the log and return the entries just added."""
    timestamp = datetime.now().astimezone().isoformat(timespec="seconds")
    entries = [{"timestamp": timestamp, **result} for result in results]

    config.ensure_config_dir()
    config.SENT_LOG_PATH.write_text(json.dumps(read() + entries, indent=2))
    return entries


def already_sent_to(email):
    """Whether this address has been mailed before — guards against double sends."""
    target = email.strip().lower()
    return any(
        (entry.get("to") or "").strip().lower() == target and entry.get("success")
        for entry in read()
    )
