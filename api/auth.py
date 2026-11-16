import hashlib
import hmac
import os
import re
import secrets
import time
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, Field

from services.database import connect, initialize_database, mongo_db, require_persistent_store, uses_mongodb

router = APIRouter(prefix="/api/auth", tags=["authentication"])
COOKIE_NAME = "clarity_session"
SESSION_SECONDS = 60 * 60 * 24 * 30
PBKDF2_ROUNDS = 310_000
initialize_database()


class Credentials(BaseModel):
    email: str = Field(min_length=5, max_length=254)
    password: str = Field(min_length=8, max_length=128)


def _hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PBKDF2_ROUNDS)
    return f"{salt.hex()}:{key.hex()}"


def _check_password(password: str, stored: str) -> bool:
    try:
        salt_hex, key_hex = stored.split(":", 1)
        calculated = _hash_password(password, bytes.fromhex(salt_hex)).split(":", 1)[1]
        return hmac.compare_digest(calculated, key_hex)
    except (ValueError, TypeError):
        return False


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _set_session(response: Response, user_id: str) -> None:
    token = secrets.token_urlsafe(40)
    if uses_mongodb():
        mongo_db().sessions.insert_one({
            "token_hash": _token_hash(token), "user_id": user_id,
            "expires_at": datetime.now(timezone.utc) + timedelta(seconds=SESSION_SECONDS),
        })
    else:
        with connect() as db:
            db.execute("DELETE FROM sessions WHERE expires_at < ?", (int(time.time()),))
            db.execute("INSERT INTO sessions(token_hash,user_id,expires_at) VALUES(?,?,?)",
                       (_token_hash(token), user_id, int(time.time()) + SESSION_SECONDS))
    response.set_cookie(COOKIE_NAME, token, max_age=SESSION_SECONDS, httponly=True,
                        secure=os.getenv("VERCEL") == "1", samesite="lax", path="/")


def current_user(request: Request):
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return None
    if uses_mongodb():
        db = mongo_db()
        session = db.sessions.find_one({"token_hash": _token_hash(token),
                                        "expires_at": {"$gt": datetime.now(timezone.utc)}})
        return db.users.find_one({"id": session["user_id"]}, {"_id": 0, "id": 1, "email": 1}) if session else None
    with connect() as db:
        row = db.execute("""SELECT u.id,u.email FROM sessions s JOIN users u ON u.id=s.user_id
                            WHERE s.token_hash=? AND s.expires_at>?""",
                         (_token_hash(token), int(time.time()))).fetchone()
    return dict(row) if row else None


def require_user(request: Request):
    user = current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Sign in to continue")
    return user


@router.post("/signup")
def signup(payload: Credentials, response: Response):
    require_persistent_store()
    email = payload.email.strip().lower()
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
        raise HTTPException(status_code=422, detail="Enter a valid email address")
    user_id = str(uuid4())
    try:
        if uses_mongodb():
            mongo_db().users.insert_one({"id": user_id, "email": email,
                "password_hash": _hash_password(payload.password), "created_at": datetime.now(timezone.utc)})
        else:
            with connect() as db:
                db.execute("INSERT INTO users(id,email,password_hash) VALUES(?,?,?)",
                           (user_id, email, _hash_password(payload.password)))
    except Exception as exc:
        if "UNIQUE constraint failed" in str(exc) or exc.__class__.__name__ == "DuplicateKeyError":
            raise HTTPException(status_code=409, detail="An account with this email already exists") from exc
        raise
    _set_session(response, user_id)
    return {"user": {"id": user_id, "email": email}}


@router.post("/login")
def login(payload: Credentials, response: Response):
    require_persistent_store()
    email = payload.email.strip().lower()
    if uses_mongodb():
        user = mongo_db().users.find_one({"email": email}, {"_id": 0, "id": 1, "email": 1, "password_hash": 1})
    else:
        with connect() as db:
            user = db.execute("SELECT id,email,password_hash FROM users WHERE email=?", (email,)).fetchone()
    if not user or not _check_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Email or password is incorrect")
    _set_session(response, user["id"])
    return {"user": {"id": user["id"], "email": user["email"]}}


@router.get("/session")
def session(request: Request):
    return {"user": current_user(request)}


@router.post("/logout")
def logout(request: Request, response: Response):
    token = request.cookies.get(COOKIE_NAME)
    if token:
        if uses_mongodb():
            mongo_db().sessions.delete_one({"token_hash": _token_hash(token)})
        else:
            with connect() as db:
                db.execute("DELETE FROM sessions WHERE token_hash=?", (_token_hash(token),))
    response.delete_cookie(COOKIE_NAME, path="/", httponly=True, samesite="lax")
    return {"ok": True}
