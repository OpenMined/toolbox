import sqlite3

from pydantic import BaseModel, EmailStr


class UserRegistration(BaseModel):
    email: EmailStr
    access_token: str


class User(BaseModel):
    id: int
    email: EmailStr
    access_token: str

    @classmethod
    def from_sqlite_row(cls, row: sqlite3.Row):
        return cls(
            id=row["id"],
            email=row["email"],
            access_token=row["access_token"],
        )


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    message: str
