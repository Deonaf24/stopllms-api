from fastapi import Depends, HTTPException, status
from jose import JWTError, jwt

from app.core.config import settings
from app.core.db import get_db
from app.core.security import get_user, oauth2_scheme
from app.schemas.auth import TokenData, User


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credential_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str | None = payload.get("sub")
        if email is None:
            raise credential_exception

        token_data = TokenData(email=email)

    except JWTError:
        raise credential_exception

    user = get_user(email=token_data.email)
    if user is None:
        raise credential_exception

    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")

    return current_user


__all__ = ["get_db", "get_current_active_user", "get_current_user"]
