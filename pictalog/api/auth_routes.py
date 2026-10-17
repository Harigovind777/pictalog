from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from pictalog.auth import create_token, current_user, hash_password, verify_password
from pictalog.db import get_db
from pictalog.models import User
from pictalog.schemas import AuthOut, LoginIn, SignupIn, UserOut, UserUpdate

router = APIRouter(prefix="/api/auth")


def _auth_out(request: Request, user: User) -> AuthOut:
    settings = request.app.state.settings
    return AuthOut(token=create_token(user.id, settings.secret_key, settings.token_days), user=UserOut.of(user))


@router.post("/signup", status_code=201)
def signup(body: SignupIn, request: Request, db: Session = Depends(get_db)) -> AuthOut:
    email = body.email.lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(409, "An account with this email already exists.")
    user = User(email=email, password_hash=hash_password(body.password), company_name=body.company_name.strip())
    db.add(user)
    db.commit()
    return _auth_out(request, user)


@router.post("/login")
def login(body: LoginIn, request: Request, db: Session = Depends(get_db)) -> AuthOut:
    user = db.scalar(select(User).where(User.email == body.email.lower()))
    if user is None or not verify_password(user.password_hash, body.password):
        raise HTTPException(401, "Wrong email or password.")
    return _auth_out(request, user)


@router.get("/me")
def me(user: User = Depends(current_user)) -> UserOut:
    return UserOut.of(user)


@router.patch("/me")
def update_me(body: UserUpdate, user: User = Depends(current_user), db: Session = Depends(get_db)) -> UserOut:
    user.company_name = body.company_name.strip()
    db.commit()
    return UserOut.of(user)
