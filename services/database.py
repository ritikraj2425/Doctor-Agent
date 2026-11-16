"""Persistence adapter: local MongoDB when configured, SQLite as a local fallback."""
import os
import sqlite3
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

_mongo_client = None
_mongo_indexes_ready = False


def uses_mongodb() -> bool:
    return bool(os.getenv("MONGODB_URI"))


def require_persistent_store() -> None:
    if os.getenv("VERCEL") == "1" and not uses_mongodb():
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail="Set MONGODB_URI in Vercel to enable persistent accounts and chat history")


def mongo_db():
    global _mongo_client, _mongo_indexes_ready
    if not uses_mongodb():
        raise RuntimeError("Set MONGODB_URI to use MongoDB persistence")
    if _mongo_client is None:
        from pymongo import MongoClient
        _mongo_client = MongoClient(os.environ["MONGODB_URI"],
                                   serverSelectionTimeoutMS=8000,
                                   connectTimeoutMS=8000,
                                   maxPoolSize=10)
    db = _mongo_client[os.getenv("MONGODB_DATABASE", "clarity")]
    if not _mongo_indexes_ready:
        db.users.create_index("email", unique=True)
        db.sessions.create_index("token_hash", unique=True)
        db.sessions.create_index("expires_at", expireAfterSeconds=0)
        db.chats.create_index([("owner_id", 1), ("updated_at", -1)])
        db.messages.create_index([("chat_id", 1), ("created_at", 1)])
        _mongo_indexes_ready = True
    return db


def database_path() -> Path:
    configured = os.getenv("DATABASE_PATH")
    if configured:
        return Path(configured)
    if os.getenv("VERCEL"):
        return Path("/tmp/clarity.sqlite3")
    return Path(__file__).resolve().parent.parent / "data" / "clarity.sqlite3"


def connect() -> sqlite3.Connection:
    path = database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=20)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 20000")
    return conn


def initialize_database() -> None:
    if os.getenv("VERCEL") == "1" and not uses_mongodb():
        return
    if uses_mongodb():
        return
    with connect() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS users (
          id TEXT PRIMARY KEY,
          email TEXT NOT NULL UNIQUE COLLATE NOCASE,
          password_hash TEXT NOT NULL,
          created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
        );
        CREATE TABLE IF NOT EXISTS sessions (
          token_hash TEXT PRIMARY KEY,
          user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          expires_at INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS chats (
          id TEXT PRIMARY KEY,
          owner_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          title TEXT NOT NULL DEFAULT 'New conversation',
          created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
          updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
        );
        CREATE TABLE IF NOT EXISTS messages (
          id TEXT PRIMARY KEY,
          chat_id TEXT NOT NULL REFERENCES chats(id) ON DELETE CASCADE,
          role TEXT NOT NULL CHECK(role IN ('user','assistant')),
          content TEXT NOT NULL,
          metadata TEXT NOT NULL DEFAULT '{}',
          created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
        );
        CREATE INDEX IF NOT EXISTS chats_owner_updated ON chats(owner_id, updated_at DESC);
        CREATE INDEX IF NOT EXISTS messages_chat_created ON messages(chat_id, created_at);
        """)
