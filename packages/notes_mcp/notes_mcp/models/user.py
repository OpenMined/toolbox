from pydantic import BaseModel, EmailStr


class UserRegistration(BaseModel):
    email: EmailStr
    access_token: str


class User(BaseModel):
    id: int
    email: EmailStr
    access_token: str


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    message: str
