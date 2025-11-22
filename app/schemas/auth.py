from pydantic import BaseModel, EmailStr

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None

class User(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None
    hashed_password: str
    disabled: bool | None = None

class UserCreate(BaseModel):
    username: str
    full_name: str
    email: EmailStr
    password: str
    password_confirm: str
    is_teacher: bool