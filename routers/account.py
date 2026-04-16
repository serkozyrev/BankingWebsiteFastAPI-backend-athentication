from typing import List

from fastapi import APIRouter, Query
from fastapi.params import Depends
from sqlalchemy.orm import Session

from auth.oAuth2 import get_current_user
from db import db_account
from db.database import get_db
from routers.schemas import AccountBase, RecordBase, AccountRecordBase, UserAuth

router = APIRouter(
    prefix="/account",
    tags=["account"],
)

@router.post('')
def add_account(request:AccountBase, db: Session = Depends(get_db), current_user:UserAuth=Depends(get_current_user)):
    return db_account.add_account(request, db, current_user.user_id)

@router.get('/all')
def get_all_accounts(db: Session = Depends(get_db), current_user:UserAuth=Depends(get_current_user)):
    return db_account.get_all_accounts(db, current_user.user_id)

# @router.post("/copyrecord")
# def copy_expense_record(request: RecordBase, db:Session = Depends(get_db), current_user:UserAuth=Depends(get_current_user)):
#     return db_expense.copy_record(request, db, current_user.user_id)
#
# @router.put("/editrecord")
# def edit_expense_record(request: EditExpenseRecord, db:Session = Depends(get_db), current_user:UserAuth=Depends(get_current_user)):
#     return db_expense.edit_expense_record(request, db, current_user.user_id)

@router.post("/deleterecord")
def delete_account_record(request: AccountRecordBase, db:Session = Depends(get_db), current_user:UserAuth=Depends(get_current_user)):
    return db_account.delete_account_record(request, db, current_user.user_id)