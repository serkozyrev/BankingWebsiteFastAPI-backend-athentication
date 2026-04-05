from http.client import HTTPException

from sqlalchemy.orm import Session

from db.hash import Hash
from db.models import DbUser, DbAccount, DbCategories
from routers.schemas import UserBase
from fastapi import HTTPException, status


def create_user(db:Session, request:UserBase):
    existing_user = db.query(DbUser).filter(DbUser.email == request.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")
    new_user = DbUser(
        username=request.username,
        email=request.email,
        password= Hash.bcrypt(request.password)
    )
    db.add(new_user)
    db.commit()

    db.refresh(new_user)

    default_accounts = [
        DbAccount(user_id=new_user.user_id, description="Visa", user_balance=0),
        DbAccount(user_id=new_user.user_id, description="Chequing", user_balance=0),
        DbAccount(user_id=new_user.user_id, description="LineOfCredit", user_balance=0),
    ]
    default_category=[
                    DbCategories(user_id=new_user.user_id, description="Other", category_name="other")
    ]

    db.add_all(default_accounts)
    db.add(default_category)
    db.commit()
    return new_user

def get_all_users(db:Session):
    return db.query(DbUser).all()

def get_user(db:Session, user_id:int):
    user= db.query(DbUser).filter(DbUser.user_id==user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user

def get_user_by_username(db:Session, username:str):
    user= db.query(DbUser).filter(DbUser.username==username).first()
    # print('user', user)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user

def delete_user(db:Session, id:int):
    user = db.query(DbUser).get(id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    db.delete(user)
    db.commit()
    return 'user deleted'