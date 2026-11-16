import json
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from api.auth import require_user
from services.database import connect, mongo_db, require_persistent_store, uses_mongodb

router = APIRouter(prefix="/api/chats", tags=["chats"])


class NewChat(BaseModel):
    title: str = Field(default="New conversation", max_length=160)


class NewMessage(BaseModel):
    role: str
    content: str = Field(max_length=100_000)
    metadata: dict = Field(default_factory=dict)


@router.get("")
def list_chats(request: Request):
    require_persistent_store()
    user = require_user(request)
    if uses_mongodb():
        return list(mongo_db().chats.find({"owner_id": user["id"]}, {"_id": 0}).sort("updated_at", -1))
    with connect() as db:
        rows = db.execute("SELECT id,title,created_at,updated_at FROM chats WHERE owner_id=? ORDER BY updated_at DESC",
                          (user["id"],)).fetchall()
    return [dict(row) for row in rows]


@router.post("")
def create_chat(payload: NewChat, request: Request):
    require_persistent_store()
    user = require_user(request)
    chat_id = str(uuid4())
    title = payload.title.strip() or "New conversation"
    now = datetime.now(timezone.utc).isoformat()
    if uses_mongodb():
        chat = {"id": chat_id, "owner_id": user["id"], "title": title, "created_at": now, "updated_at": now}
        mongo_db().chats.insert_one(chat)
        # PyMongo inserts its generated ObjectId into the same dict. Never
        # return that value directly because FastAPI's JSON encoder cannot
        # serialize bson.ObjectId.
        return {k: v for k, v in chat.items() if k not in ("owner_id", "_id")}
    with connect() as db:
        db.execute("INSERT INTO chats(id,owner_id,title) VALUES(?,?,?)", (chat_id, user["id"], title))
        row = db.execute("SELECT id,title,created_at,updated_at FROM chats WHERE id=?", (chat_id,)).fetchone()
    return dict(row)


@router.delete("/{chat_id}")
def delete_chat(chat_id: str, request: Request):
    require_persistent_store()
    user = require_user(request)
    if uses_mongodb():
        db = mongo_db()
        owned = db.chats.find_one({"id": chat_id, "owner_id": user["id"]}, {"_id": 1})
        if not owned:
            raise HTTPException(status_code=404, detail="Chat not found")
        db.messages.delete_many({"chat_id": chat_id})
        db.chats.delete_one({"id": chat_id, "owner_id": user["id"]})
        return {"ok": True}
    with connect() as db:
        deleted = db.execute("DELETE FROM chats WHERE id=? AND owner_id=?", (chat_id, user["id"]))
        if not deleted.rowcount:
            raise HTTPException(status_code=404, detail="Chat not found")
    return {"ok": True}


@router.get("/{chat_id}/messages")
def list_messages(chat_id: str, request: Request):
    require_persistent_store()
    user = require_user(request)
    if uses_mongodb():
        db = mongo_db()
        if not db.chats.find_one({"id": chat_id, "owner_id": user["id"]}, {"_id": 1}):
            raise HTTPException(status_code=404, detail="Chat not found")
        return list(db.messages.find({"chat_id": chat_id}, {"_id": 0}).sort("created_at", 1))
    with connect() as db:
        owned = db.execute("SELECT 1 FROM chats WHERE id=? AND owner_id=?", (chat_id, user["id"])).fetchone()
        if not owned:
            raise HTTPException(status_code=404, detail="Chat not found")
        rows = db.execute("SELECT id,role,content,metadata,created_at FROM messages WHERE chat_id=? ORDER BY rowid",
                          (chat_id,)).fetchall()
    result = []
    for row in rows:
        item = dict(row)
        item["metadata"] = json.loads(item["metadata"] or "{}")
        result.append(item)
    return result


@router.post("/{chat_id}/messages")
def create_message(chat_id: str, payload: NewMessage, request: Request):
    require_persistent_store()
    user = require_user(request)
    if payload.role not in ("user", "assistant"):
        raise HTTPException(status_code=422, detail="Invalid message role")
    message_id = str(uuid4())
    now = datetime.now(timezone.utc).isoformat()
    if uses_mongodb():
        db = mongo_db()
        chat = db.chats.find_one({"id": chat_id, "owner_id": user["id"]}, {"_id": 0, "title": 1})
        if not chat:
            raise HTTPException(status_code=404, detail="Chat not found")
        title = chat["title"]
        if payload.role == "user" and title == "New conversation":
            title = payload.content[:48] + ("…" if len(payload.content) > 48 else "")
        db.messages.insert_one({"id": message_id, "chat_id": chat_id, "role": payload.role,
                                "content": payload.content, "metadata": payload.metadata, "created_at": now})
        db.chats.update_one({"id": chat_id, "owner_id": user["id"]},
                            {"$set": {"title": title, "updated_at": now}})
        return {"id": message_id, "chat_id": chat_id, "role": payload.role, "content": payload.content,
                "metadata": payload.metadata, "created_at": now}
    with connect() as db:
        chat = db.execute("SELECT title FROM chats WHERE id=? AND owner_id=?", (chat_id, user["id"])).fetchone()
        if not chat:
            raise HTTPException(status_code=404, detail="Chat not found")
        title = chat["title"]
        if payload.role == "user" and title == "New conversation":
            title = payload.content[:48] + ("…" if len(payload.content) > 48 else "")
        db.execute("INSERT INTO messages(id,chat_id,role,content,metadata) VALUES(?,?,?,?,?)",
                   (message_id, chat_id, payload.role, payload.content, json.dumps(payload.metadata, ensure_ascii=False)))
        db.execute("UPDATE chats SET title=?,updated_at=strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id=?",
                   (title, chat_id))
    return {"id": message_id, "chat_id": chat_id, "role": payload.role, "content": payload.content,
            "metadata": payload.metadata, "created_at": now}
