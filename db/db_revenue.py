import string, random, shutil

from fastapi import HTTPException, status
from decimal import Decimal
from sqlalchemy import cast, desc, Integer

from routers.schemas import RevenueBase, RecordBase, EditRevenueRecord
from sqlalchemy.orm import Session
from db.models import DbRevenue, DbAccount
import datetime
from helpers import information

def add_revenue(request: RevenueBase, db: Session, user_id: int):
    print(request)

    request_date=request.date
    day=request_date.day
    month=request_date.month
    year=request_date.year

    revenue_post=DbRevenue(
        user_id=user_id,
        description=request.description,
        revenue_balance = request.revenue_balance,
        transaction_day = day,
        transaction_month = month,
        transaction_year = year,
        category = request.category,
        transaction_type = request.transaction_type
    )
    db.add(revenue_post)

    if request.category == 'chequing':
        chequing_acc = db.query(DbAccount).filter(DbAccount.user_id == user_id,
                                                  DbAccount.description == "Chequing").first()
        if not chequing_acc:
            raise HTTPException(status_code=404, detail="Chequing not found")

        new_balance=chequing_acc.user_balance+ request.revenue_balance
        chequing_acc.user_balance=round(new_balance,2)
        print(chequing_acc.user_balance)
        db.add(chequing_acc)
    elif request.category == 'visa':
        visa_acc = db.query(DbAccount).filter(DbAccount.user_id == user_id,
                                              DbAccount.description == "Visa").first()
        if not visa_acc:
            raise HTTPException(status_code=404, detail="Visa account not found")

        new_balance = visa_acc.user_balance + request.revenue_balance
        visa_acc.user_balance = round(new_balance, 2)
        db.add(visa_acc)
    elif request.category == 'lineofcredit':
        line_of_credit_acc = db.query(DbAccount).filter(DbAccount.user_id == user_id,
                                                        DbAccount.description == "LineOfCredit").first()
        if not line_of_credit_acc:
            raise HTTPException(status_code=404, detail="Visa account not found")

        new_balance = line_of_credit_acc.user_balance + request.revenue_balance
        line_of_credit_acc.user_balance = round(new_balance, 2)
        db.add(line_of_credit_acc)
    db.commit()
    db.refresh(revenue_post) #'account_info':account_info
    return get_all_revenue(db, user_id)

def get_all_revenue(db: Session, user_id:int):
    revenues = db.query(DbRevenue).where(DbRevenue.user_id== user_id).order_by(
        desc(cast(DbRevenue.transaction_year, Integer)),
        desc(cast(DbRevenue.transaction_month, Integer)),
        desc(cast(DbRevenue.transaction_day, Integer))
    ).all()
    revenues_list=[
        {
            'id': revenue.revenue_id,
            'description': revenue.description,
            'amount': revenue.revenue_balance,
            'day': revenue.transaction_day,
            'month': revenue.transaction_month,
            'year': revenue.transaction_year
        }
        for revenue in revenues
    ]
    account_info=information.collect_information(db, user_id)
    return {'message': 'Record Saved Successfully', 'revenues':revenues_list, 'account_info':account_info}

def copy_record(request:RecordBase, db:Session, user_id: int):
    date=datetime.date.today()
    day = date.day
    month = date.month
    year = date.year

    revenue_record=db.query(DbRevenue).filter(
        DbRevenue.expense_id == request.id,
        DbRevenue.user_id == user_id
    ).first()
    if revenue_record is None:
        raise HTTPException(status_code=404, detail="Record not found")
    revenue_post = DbRevenue(
        user_id=user_id,
        description=revenue_record.description,
        revenue_balance=revenue_record.revenue_balance,
        transaction_day=day,
        transaction_month=month,
        transaction_year=year,
        category=revenue_record.category,
        transaction_type=revenue_record.transaction_type
    )
    # print(revenue_post)
    db.add(revenue_post)
    if revenue_record.category == 'chequing':
        chequing_acc = db.query(DbAccount).filter(DbAccount.user_id == user_id,
                                                  DbAccount.description == "Chequing").first()
        if not chequing_acc:
            raise HTTPException(status_code=404, detail="Chequing not found")

        new_balance=chequing_acc.user_balance+ revenue_record.revenue_balance
        chequing_acc.user_balance=round(new_balance,2)
        db.add(chequing_acc)
    elif revenue_record.category == 'visa':
        visa_acc = db.query(DbAccount).filter(DbAccount.user_id == user_id,
                                              DbAccount.description == "Visa").first()
        if not visa_acc:
            raise HTTPException(status_code=404, detail="Visa account not found")

        new_balance = visa_acc.user_balance + revenue_record.revenue_balance
        visa_acc.user_balance = round(new_balance, 2)
        db.add(visa_acc)
    db.commit() #'account_info':account_info
    db.refresh(revenue_post)
    return get_all_revenue(db, user_id)


def edit_revenue_record(request:EditRevenueRecord, db:Session, user_id:int):
    revenue_item=db.get(DbRevenue, request.id)
    if not revenue_item:
        raise HTTPException(status_code=404, detail="Revenue record not found")
    data=request.model_dump(exclude_unset=True)
    chequing_acc = db.query(DbAccount).filter(DbAccount.user_id == user_id,
                                              DbAccount.description == "Chequing").first()
    visa_acc = db.query(DbAccount).filter(DbAccount.user_id == user_id,
                                          DbAccount.description == "Visa").first()
    new_amount=data.get('revenue_balance')
    old_balance=revenue_item.revenue_balance

    print('database revenue_balance',revenue_item.revenue_balance, 'request revenue_balance', data['revenue_balance'])
    if data.get('category') == 'chequing':
        new_balance=(chequing_acc.user_balance-old_balance)+new_amount
        chequing_acc.user_balance=round(new_balance,2)
        db.add(chequing_acc)
    else:
        new_balance = (visa_acc.user_balance - old_balance) + new_amount
        visa_acc.user_balance = round(new_balance, 2)
        db.add(visa_acc)

    for key, value in data.items():
        setattr(revenue_item, key, value)
    db.commit()
    db.refresh(revenue_item)
    return get_all_revenue(db, user_id)


def delete_revenue_record(request:RecordBase, db:Session, user_id:int):
    revenue_item=db.get(DbRevenue, request.id)
    if not revenue_item:
        raise HTTPException(status_code=404, detail="Revenue record not found")
    chequing_acc = db.query(DbAccount).filter(DbAccount.user_id == user_id,
                                              DbAccount.description == "Chequing").first()
    visa_acc = db.query(DbAccount).filter(DbAccount.user_id == user_id,
                                          DbAccount.description == "Visa").first()
    if revenue_item.category == 'chequing':
        chequing_acc.user_balance = chequing_acc.user_balance- revenue_item.revenue_balance
        db.add(chequing_acc)
    else:
        visa_acc.user_balance = visa_acc.user_balance - revenue_item.revenue_balance
        db.add(visa_acc)
    db.delete(revenue_item)
    db.commit()
    return get_all_revenue(db, user_id)