import os

from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from typing import Optional
from jose import jwt, JWTError  # from python-jose
from datetime import datetime, timedelta, UTC
import secrets, binascii
from fastapi.params import Depends
from sqlalchemy.orm import Session

from db import models, db_user
from db.database import get_db

oAuth2_schema = OAuth2PasswordBearer(tokenUrl="login")
client_secret_key = os.getenv("CLIENT_SECRET_KEY")
ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 60

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, client_secret_key, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(token: str= Depends(oAuth2_schema), db: Session=Depends(get_db)):
    credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                          detail="Could not validate credentials",
                                          headers={"WWW-Authenticate": "Bearer"})
    # client_secret = generate_oauth_secret()
    try:
        payload=jwt.decode(token, client_secret_key, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")

        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db_user.get_user(db, user_id)

    if user is None:
        raise credentials_exception
    return user