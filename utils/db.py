"""
Database abstraction layer for the new Anime systems.
Supports MongoDB if available, otherwise falls back to local JSON.
"""

import json
import os
import threading
import pymongo

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.environ.get("DATA_DIR", os.path.join(BASE_DIR, "data"))

# Setup MongoDB if URI exists
MONGO_URI = os.environ.get("MONGO_URI")
if MONGO_URI:
    try:
        mongo_client = pymongo.MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        mongo_client.server_info()
        db = mongo_client["zenbot"]
    except Exception:
        db = None
else:
    db = None

_json_locks: dict[str, threading.Lock] = {}


def _get_lock(collection_name: str) -> threading.Lock:
    if collection_name not in _json_locks:
        _json_locks[collection_name] = threading.Lock()
    return _json_locks[collection_name]


def _get_path(collection_name: str) -> str:
    return os.path.join(DATA_DIR, f"{collection_name}.json")


def _load_json(collection_name: str) -> dict:
    path = _get_path(collection_name)
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, ValueError):
        return {}


def _save_json(collection_name: str, data: dict) -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    path = _get_path(collection_name)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, path)


# ═══════════════════════════════════════════════════════════════════════════════
#  CORE DB OPERATIONS
# ═══════════════════════════════════════════════════════════════════════════════

def get_doc(collection_name: str, doc_id: str | int, default_factory=dict) -> dict:
    """Retrieve a document by ID."""
    uid = str(doc_id)
    if db is not None:
        doc = db[collection_name].find_one({"_id": uid})
        if doc:
            return doc
        return default_factory()
    
    with _get_lock(collection_name):
        data = _load_json(collection_name)
        return data.get(uid, default_factory())


def update_doc(collection_name: str, doc_id: str | int, update_data: dict) -> None:
    """Update a document by ID (MongoDB $set style merging for JSON)."""
    uid = str(doc_id)
    if db is not None:
        db[collection_name].update_one({"_id": uid}, {"$set": update_data}, upsert=True)
        return

    with _get_lock(collection_name):
        data = _load_json(collection_name)
        if uid not in data:
            data[uid] = {}
        data[uid].update(update_data)
        _save_json(collection_name, data)


def save_doc(collection_name: str, doc_id: str | int, full_doc: dict) -> None:
    """Completely overwrite a document by ID."""
    uid = str(doc_id)
    if db is not None:
        full_doc["_id"] = uid
        db[collection_name].replace_one({"_id": uid}, full_doc, upsert=True)
        return

    with _get_lock(collection_name):
        data = _load_json(collection_name)
        data[uid] = full_doc
        _save_json(collection_name, data)


def increment_field(collection_name: str, doc_id: str | int, field_name: str, amount: int = 1, default: int = 0) -> int:
    """Increment a numeric field and return the new value."""
    uid = str(doc_id)
    if db is not None:
        res = db[collection_name].find_one_and_update(
            {"_id": uid},
            {"$inc": {field_name: amount}},
            upsert=True,
            return_document=pymongo.ReturnDocument.AFTER
        )
        return res[field_name]

    with _get_lock(collection_name):
        data = _load_json(collection_name)
        if uid not in data:
            data[uid] = {}
        current = data[uid].get(field_name, default)
        new_val = current + amount
        data[uid][field_name] = new_val
        _save_json(collection_name, data)
        return new_val


def append_to_list(collection_name: str, doc_id: str | int, field_name: str, item: any) -> None:
    """Append an item to a list field."""
    uid = str(doc_id)
    if db is not None:
        db[collection_name].update_one({"_id": uid}, {"$push": {field_name: item}}, upsert=True)
        return

    with _get_lock(collection_name):
        data = _load_json(collection_name)
        if uid not in data:
            data[uid] = {}
        if field_name not in data[uid]:
            data[uid][field_name] = []
        data[uid][field_name].append(item)
        _save_json(collection_name, data)


def remove_from_list(collection_name: str, doc_id: str | int, field_name: str, item: any) -> None:
    """Remove an item from a list field."""
    uid = str(doc_id)
    if db is not None:
        db[collection_name].update_one({"_id": uid}, {"$pull": {field_name: item}})
        return

    with _get_lock(collection_name):
        data = _load_json(collection_name)
        if uid in data and field_name in data[uid]:
            try:
                data[uid][field_name].remove(item)
                _save_json(collection_name, data)
            except ValueError:
                pass


def get_all(collection_name: str) -> dict:
    """Get all documents in a collection."""
    if db is not None:
        cursor = db[collection_name].find()
        return {doc["_id"]: doc for doc in cursor}
    
    with _get_lock(collection_name):
        return _load_json(collection_name)
