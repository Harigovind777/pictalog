from datetime import UTC, datetime, timedelta

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError
from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from pictalog.db import get_db
from pictalog.models import User

_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except VerificationError:
        return False


def create_token(user_id: int, secret: str, days: int) -> str:
    payload = {"sub": str(user_id), "exp": datetime.now(UTC) + timedelta(days=days)}
    return jwt.encode(payload, secret, algorithm="HS256")


def _unauthorized() -> HTTPException:
    return HTTPException(status_code=401, detail="Please sign in again.")


def current_user(request: Request, db: Session = Depends(get_db)) -> User:
    header = request.headers.get("authorization", "")
    scheme, _, token = header.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise _unauthorized()
    try:
        payload = jwt.decode(token, request.app.state.settings.secret_key, algorithms=["HS256"])
        user_id = int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise _unauthorized() from None
    user = db.get(User, user_id)
    if user is None:
        raise _unauthorized()
    return user
