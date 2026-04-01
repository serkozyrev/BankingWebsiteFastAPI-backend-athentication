from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from db.database import get_db
from db.hash import Hash
from auth import oAuth2
from db.models import DbUser

router = APIRouter(
    tags=['authentication']
)

@router.post('/login')
def get_token(request: OAuth2PasswordRequestForm=Depends(), db:Session=Depends(get_db)):
    user = db.query(DbUser).filter(DbUser.username==request.username).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")

    if not Hash.verify(user.password, request.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")

    access_token=oAuth2.create_access_token(data={"user_id":user.user_id})

    return {"access_token":access_token,"token_type":"bearer", "user_id":user.user_id, "username":user.username}