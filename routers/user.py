from typing import List

from fastapi import APIRouter
from fastapi.params import Depends
from sqlalchemy.orm import Session

from auth.oAuth2 import get_current_user
from db import db_user
from db.database import get_db
from routers.schemas import UserBase, UserDisplay, UserAuth

router = APIRouter(
    prefix="/user",
    tags=["user"]
)

#create user
@router.post("/", response_model=UserDisplay)
def create_user(request:UserBase, db:Session=Depends(get_db)):
    print(request)
    return db_user.create_user(db, request)

#read user
@router.get('/', response_model=List[UserDisplay])
def get_all_users(db:Session=Depends(get_db), current_user:UserAuth=Depends(get_current_user)):
    return db_user.get_all_users(db)

@router.get("/{user_id}", response_model=UserDisplay)
def get_user(user_id:int, db:Session=Depends(get_db), current_user:UserAuth=Depends(get_current_user)):
    return db_user.get_user(db, user_id)
#update user
# @router.put("/{user_id}/update")
# def update_user(user_id: int, request:UserBase, db:Session=Depends(get_db), current_user:UserAuth=Depends(get_current_user)):
#     return db_user.update_user(db, request, user_id)

#delete user
@router.get("/delete/{user_id}")
def delete_user(user_id: int, db:Session=Depends(get_db), current_user:UserAuth=Depends(get_current_user)):
    return db_user.delete_user(db, user_id)