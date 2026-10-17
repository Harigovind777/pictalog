from pydantic import BaseModel, EmailStr, Field

from pictalog.models import User


def file_url(key: str | None) -> str | None:
    return f"/api/files/{key}" if key else None


class SignupIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=200)
    company_name: str = Field(min_length=1, max_length=200)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    company_name: str = Field(min_length=1, max_length=200)


class UserOut(BaseModel):
    id: int
    email: str
    company_name: str
    logo_url: str | None

    @classmethod
    def of(cls, user: User) -> "UserOut":
        return cls(id=user.id, email=user.email, company_name=user.company_name, logo_url=file_url(user.logo_key))


class AuthOut(BaseModel):
    token: str
    user: UserOut
