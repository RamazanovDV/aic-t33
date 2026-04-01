import json
import os
from pathlib import Path
from typing import Optional
from app.models import Ticket, User, EmulatorConfig

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

TICKETS_FILE = DATA_DIR / "tickets.json"
USERS_FILE = DATA_DIR / "users.json"
CONFIG_FILE = DATA_DIR / "config.json"


def _load_json(path: Path, default: dict):
    if not path.exists():
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_json(path: Path, data: dict):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)


def load_tickets() -> list[Ticket]:
    data = _load_json(TICKETS_FILE, {"tickets": []})
    return [Ticket(**t) for t in data.get("tickets", [])]


def save_tickets(tickets: list[Ticket]):
    _save_json(TICKETS_FILE, {"tickets": [t.model_dump() for t in tickets]})


def load_users() -> list[User]:
    data = _load_json(USERS_FILE, {"users": []})
    return [User(**u) for u in data.get("users", [])]


def save_users(users: list[User]):
    _save_json(USERS_FILE, {"users": [u.model_dump() for u in users]})


def load_config() -> EmulatorConfig:
    data = _load_json(CONFIG_FILE, {})
    return EmulatorConfig(**data)


def save_config(config: EmulatorConfig):
    _save_json(CONFIG_FILE, config.model_dump())
