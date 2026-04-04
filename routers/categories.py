from typing import List

from fastapi import APIRouter
from fastapi.params import Depends
from sqlalchemy.orm import Session

from auth.oAuth2 import get_current_user
from db import db_categories
from db.database import get_db
from routers.schemas import CategoryBase, CategoryRecordBase, UserAuth, CategoryDisplay

router = APIRouter(
    prefix="/categories",
    tags=["categories"],
)

# image_url_types =['absolute', 'relative']

@router.post('')
def add_category(request:CategoryBase, db: Session = Depends(get_db), current_user:UserAuth=Depends(get_current_user)):

    return db_categories.add_category(request, db, current_user.user_id)

@router.get('/all', response_model=List[CategoryDisplay])
def get_all_categories(db: Session = Depends(get_db), current_user:UserAuth=Depends(get_current_user)):
    return db_categories.get_all_categories(db, current_user.user_id)

@router.post("/deleterecord")
def delete_category(request: CategoryRecordBase, db:Session = Depends(get_db), current_user:UserAuth=Depends(get_current_user)):
    return db_categories.delete_category_record(request, db, current_user.user_id)