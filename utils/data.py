"""
Persistent JSON-backed data store for player balances.

All balance operations go through this module so that saves are atomic
and cog code stays clean.
"""

import json
import os
import threading
from utils.db import db

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "data", "balances.json")

_lock = threading.Lock()  # Protect concurrent reads/writes


def _load_all() -> dict:
    """Load the full balances dict from disk."""
    if not os.path.exists(DATA_PATH):
        return {}
    with open(DATA_PATH, "r") as f:
        return json.load(f)


def _save_all(data: dict) -> None:
    """Atomically save the full balances dict to disk."""
    os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
    tmp = DATA_PATH + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, DATA_PATH)  # Atomic on most OSes


def get_balance(user_id: int, starting_balance: int = 500) -> int:
    """Return the balance for *user_id*, creating an entry if needed."""
    uid = str(user_id)
    if db is not None:
        doc = db.balances.find_one({"_id": uid})
        if not doc:
            db.balances.insert_one({"_id": uid, "bal": starting_balance})
            return starting_balance
        return doc.get("bal", starting_balance)

    with _lock:
        data = _load_all()
        if uid not in data:
            data[uid] = starting_balance
            _save_all(data)
        return data[uid]


def set_balance(user_id: int, amount: int) -> int:
    """Set *user_id*'s balance to *amount* and return it."""
    uid = str(user_id)
    new_bal = max(0, amount)
    if db is not None:
        db.balances.update_one({"_id": uid}, {"$set": {"bal": new_bal}}, upsert=True)
        return new_bal

    with _lock:
        data = _load_all()
        data[uid] = new_bal
        _save_all(data)
        return new_bal


def add_balance(user_id: int, amount: int, starting_balance: int = 500) -> int:
    """Add *amount* (can be negative) to *user_id*'s balance. Returns the new balance."""
    uid = str(user_id)
    if db is not None:
        doc = db.balances.find_one({"_id": uid})
        if not doc:
            db.balances.insert_one({"_id": uid, "bal": starting_balance})
            current = starting_balance
        else:
            current = doc.get("bal", starting_balance)
        new_bal = max(0, current + amount)
        db.balances.update_one({"_id": uid}, {"$set": {"bal": new_bal}}, upsert=True)
        return new_bal

    with _lock:
        data = _load_all()
        current = data.get(uid, starting_balance)
        new = max(0, current + amount)
        data[uid] = new
        _save_all(data)
        return new


def transfer(from_id: int, to_id: int, amount: int, starting_balance: int = 500) -> tuple[int, int]:
    """
    Transfer *amount* coins from one user to another.
    Returns (new_from_balance, new_to_balance).
    Raises ValueError if sender has insufficient funds.
    """
    f_uid, t_uid = str(from_id), str(to_id)
    if db is not None:
        from_bal = get_balance(from_id, starting_balance)
        to_bal = get_balance(to_id, starting_balance)
        if from_bal < amount:
            raise ValueError(f"Insufficient funds (have {from_bal:,}, need {amount:,}).")
        new_f = set_balance(from_id, from_bal - amount)
        new_t = set_balance(to_id, to_bal + amount)
        return new_f, new_t

    with _lock:
        data = _load_all()
        from_bal = data.get(f_uid, starting_balance)
        to_bal = data.get(t_uid, starting_balance)

        if from_bal < amount:
            raise ValueError(f"Insufficient funds (have {from_bal:,}, need {amount:,}).")

        data[f_uid] = from_bal - amount
        data[t_uid] = to_bal + amount
        _save_all(data)
        return data[f_uid], data[t_uid]


def get_leaderboard(top_n: int = 10) -> list[tuple[str, int]]:
    """Return the top *top_n* users sorted by balance descending."""
    if db is not None:
        cursor = db.balances.find().sort("bal", -1).limit(top_n)
        return [(doc["_id"], doc.get("bal", 0)) for doc in cursor]

    data = _load_all()
    sorted_data = sorted(data.items(), key=lambda x: x[1], reverse=True)
    return sorted_data[:top_n]
