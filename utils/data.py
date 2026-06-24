"""
Persistent JSON-backed data store for player balances.

All balance operations go through this module so that saves are atomic
and cog code stays clean.
"""

import json
import os
import threading

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
    with _lock:
        data = _load_all()
        uid = str(user_id)
        if uid not in data:
            data[uid] = starting_balance
            _save_all(data)
        return data[uid]


def set_balance(user_id: int, amount: int) -> int:
    """Set *user_id*'s balance to *amount* and return it."""
    with _lock:
        data = _load_all()
        data[str(user_id)] = max(0, amount)
        _save_all(data)
        return data[str(user_id)]


def add_balance(user_id: int, amount: int, starting_balance: int = 500) -> int:
    """Add *amount* (can be negative) to *user_id*'s balance. Returns the new balance."""
    with _lock:
        data = _load_all()
        uid = str(user_id)
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
    with _lock:
        data = _load_all()
        f_uid, t_uid = str(from_id), str(to_id)
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
    data = _load_all()
    sorted_data = sorted(data.items(), key=lambda x: x[1], reverse=True)
    return sorted_data[:top_n]
