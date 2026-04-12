import string, random, shutil

from fastapi import HTTPException, status, Query
from decimal import Decimal
from sqlalchemy import cast, desc, Integer, select, func
from sqlalchemy.testing.pickleable import User

from routers.schemas import AccountBase
from sqlalchemy.orm import Session
from db.models import DbAccount
import datetime
from db import db_expense

def add_account(request: AccountBase, db: Session, user_id: int):
    existing_account = db.query(DbAccount).filter(DbAccount.user_id == user_id,
                                                      DbAccount.description == request.description).first()
    if existing_account:
        raise HTTPException(status_code=400, detail="Category already exists")

    account_post=DbAccount(
        user_id=user_id,
        description=request.description,
        user_balance = request.user_balance,
        account_kind = request.account_kind
    )
    db.add(account_post)
    db.commit()
    db.refresh(account_post)
    account_info=db_expense.get_all_expense(db, user_id)#'account_info':account_info
    return {'message': 'Account created successfully', 'accounts':account_info}