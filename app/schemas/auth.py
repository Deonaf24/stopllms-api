from pydantic import BaseModel, EmailStr

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: str | None = None

# --------------------
# PUBLIC SCHEMAS
# --------------------

class User(BaseModel):
    id: int
    username: str | None = None
    email: EmailStr
    first_name: str | None = None
    last_name: str | None = None
    is_teacher: bool
    disabled: bool

# --------------------
# INPUT SCHEMAS
# --------------------

class UserCreate(BaseModel):
    username: str | None = None # Deprecated
    first_name: str
    last_name: str
    email: EmailStr
    password: str
    is_teacher: bool

class GoogleLoginRequest(BaseModel):
    id_token: str | None = None
    code: str | None = None
    is_teacher: bool = False # Optional, mainly for new registrations
    is_signup: bool = False # Must be True to allow new user creation
