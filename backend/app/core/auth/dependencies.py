from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import Optional
from jose import JWTError, jwt
from datetime import datetime, timedelta
import os

from app.core.database import get_db
from app.models import models
from app.curd.crud import user_crud

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Optional OAuth2 scheme for development/testing
class OptionalOAuth2PasswordBearer(OAuth2PasswordBearer):
    async def __call__(self, request):
        try:
            return await super().__call__(request)
        except HTTPException:
            return None
            
oauth2_scheme_optional = OptionalOAuth2PasswordBearer(tokenUrl="token")

# For demo purposes - in production, use proper secret key management
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """
    Create a JWT access token
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    Get the current user from the JWT token
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = user_crud.get_user(db, user_id=user_id)
    if user is None:
        raise credentials_exception
    return user

async def get_current_user_optional(token: Optional[str] = Depends(oauth2_scheme_optional), db: Session = Depends(get_db)):
    """
    Get the current user from the JWT token, but don't require authentication
    This is useful for development and testing purposes
    """
    try:
        return await get_current_user(token, db)
    except HTTPException:
        # For development/testing, create a dummy admin user
        return models.User(id="00000000-0000-0000-0000-000000000000", email="admin@example.com", full_name="Admin User", is_active=True)

# For development/testing - bypass authentication
def get_current_user_mock():
    """
    Mock function for development that returns a dummy user without authentication
    """
    # Create a mock user for development
    return models.User(
        id="00000000-0000-0000-0000-000000000000",
        email="dev@example.com",
        full_name="Development User",
        is_active=True,
        is_superuser=False
    )
