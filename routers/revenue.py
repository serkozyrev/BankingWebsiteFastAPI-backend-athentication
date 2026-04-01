from typing import List

from fastapi import APIRouter, HTTPException, status, File, UploadFile
from fastapi.params import Depends
from sqlalchemy.orm import Session

from auth.oAuth2 import get_current_user
from db import db_revenue
from db.database import get_db
from helpers import information
from routers.schemas import RevenueBase, RecordBase, EditRevenueRecord, UserAuth

router = APIRouter(
    prefix="/revenue",
    tags=["revenue"],
)

# image_url_types =['absolute', 'relative']

@router.post('')
def add_revenue(request:RevenueBase, db: Session = Depends(get_db), current_user:UserAuth=Depends(get_current_user)):

    return db_revenue.add_revenue(request, db, current_user.user_id)

@router.get('/all')
def get_all_revenue(db: Session = Depends(get_db), current_user:UserAuth=Depends(get_current_user)):
    return db_revenue.get_all_revenue(db, current_user.user_id)

@router.post("/copyrecord")
def copy_revenue_record(request: RecordBase, db:Session = Depends(get_db), current_user:UserAuth=Depends(get_current_user)):
    return db_revenue.copy_record(request, db, current_user.user_id)

@router.put("/editrecord")
def edit_revenue_record(request: EditRevenueRecord, db:Session = Depends(get_db), current_user:UserAuth=Depends(get_current_user)):
    return db_revenue.edit_revenue_record(request, db, current_user.user_id)

@router.post("/deleterecord")
def delete_revenue_record(request: RecordBase, db:Session = Depends(get_db), current_user:UserAuth=Depends(get_current_user)):
    return db_revenue.delete_revenue_record(request, db, current_user.user_id)
