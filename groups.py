import os
import re
from dataclasses import dataclass, field
from typing import Optional, Union

from dotenv import load_dotenv

load_dotenv()


@dataclass
class GroupConfig:
    label: str
    raw_id: str
    group: Union[int, str]
    entity: Optional[object] = field(default=None, repr=False)


def _sanitize_label(raw: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]", "_", raw.strip().lstrip("@"))


def _parse_one(entry: str) -> GroupConfig:
    entry = entry.strip()
    if ":" in entry:
        label, raw_id = entry.split(":", 1)
        label = _sanitize_label(label)
    else:
        raw_id = entry
        label = _sanitize_label(entry)
    raw_id = raw_id.strip()
    try:
        group = int(raw_id)
    except ValueError:
        group = raw_id
    return GroupConfig(label=label, raw_id=raw_id, group=group)


def load_groups() -> list:
    raw = os.environ.get("GROUPS", "")
    entries = [e for e in raw.split(",") if e.strip()]
    if not entries:
        raise SystemExit("GROUPS must be set in .env, e.g. GROUPS=jobs:@mygroup,hebrew:-100123456")
    groups = [_parse_one(e) for e in entries]
    labels = [g.label for g in groups]
    if len(labels) != len(set(labels)):
        raise SystemExit(f"Duplicate group labels in GROUPS config: {labels}")
    return groups
