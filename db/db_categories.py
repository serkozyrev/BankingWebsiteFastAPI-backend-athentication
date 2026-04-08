import string, random, shutil

from fastapi import HTTPException, status
from decimal import Decimal
from sqlalchemy import cast, desc, Integer, select, func
from sqlalchemy.testing.pickleable import User

from routers.schemas import CategoryBase, CategoryRecordBase, EditExpenseRecord
from sqlalchemy.orm import Session
from db.models import DbCategories, DbAccount
import re
import datetime
from helpers import information

def add_category(request:CategoryBase, db:Session, user_id:int):
    words = re.split(r'[\s_\-]+', request.description.lower())
    category_name=words[0] + ''.join(word.capitalize() for word in words[1:])
    existing_category = db.query(DbCategories).filter(DbCategories.user_id == user_id, DbCategories.category_name == category_name).first()
    if existing_category:
        raise HTTPException(status_code=400, detail="Category already exists")
    new_category = DbCategories(
        category_name=category_name,
        user_id=user_id,
        description=request.description,
    )
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    return {'message': 'Record Saved Successfully', 'category':new_category.category_name}

def get_all_categories(db:Session, user_id:int):
    all_categories_by_user= db.query(DbCategories).filter(DbCategories.user_id == user_id).order_by(DbCategories.category_name).all()
    # expenses_list_line_of_credit = [
    #     {
    #         'category_id': category.category_id,
    #         'description': category.description,
    #         'categoryName': category.category_name
    #     }
    #     for category in all_categories_by_user
    # ]

    # for category in all_categories_by_user:
    #     print(category)
    # return {'categories':all_categories_by_user}
    return db.query(DbCategories).filter(DbCategories.user_id == user_id).order_by(DbCategories.category_name).all()

def delete_category_record(request:CategoryRecordBase, db:Session, user_id:int):
    for record in request.category_id:
        existing_category = db.query(DbCategories).filter(DbCategories.user_id == user_id,
                                                          DbCategories.category_id == record).first()
        if existing_category:
            db.delete(existing_category)
    db.commit()
    return {'message': 'Record Deleted Successfully'}