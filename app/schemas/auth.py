from pydantic import BaseModel, EmailStr

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None

# --------------------
# PUBLIC SCHEMAS
# --------------------

class User(BaseModel):
    id: int
    username: str
    email: EmailStr
    is_teacher: bool
    disabled: bool

# --------------------
# INPUT SCHEMAS
# --------------------

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    is_teacher: bool
