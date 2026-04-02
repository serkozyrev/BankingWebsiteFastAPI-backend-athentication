import string, random, shutil

from fastapi import HTTPException, status
from decimal import Decimal
from sqlalchemy import cast, desc, Integer

from routers.schemas import RevenueBase, RecordBase, EditRevenueRecord
from sqlalchemy.orm import Session
from db.models import DbRevenue, DbAccount
import datetime
from helpers import information

TRANSFER_MAP = {
    "transferToChequing": "Chequing",
    "transferToVisa": "Visa",
    "transferToLineOfCredit": "LineOfCredit",
}

def add_sub_money(account, amount):
    account.user_balance = round(account.user_balance + amount, 2)

def apply_transfer(source, target, amount, accounts, reverse=False):
    source_acc = accounts[source]
    target_acc = accounts[target]

    # Correct financial rules
    effects = {
        ("Chequing", "Visa"): (-amount, -amount),
        ("Chequing", "LineOfCredit"): (-amount, -amount),

        ("Visa", "Chequing"): (amount, amount),
        ("LineOfCredit", "Chequing"): (amount, amount),

        ("Visa", "LineOfCredit"): (amount, -amount),
        ("LineOfCredit", "Visa"): (amount, -amount),
    }

    delta_source, delta_target = effects[(source, target)]

    if reverse:
        print(delta_source, delta_target)
        delta_source = -delta_source
        delta_target = -delta_target

    add_sub_money(source_acc, delta_source)
    add_sub_money(target_acc, delta_target)

def apply_normal(account_name, amount, accounts, reverse=False):
    acc = accounts[account_name]

    if account_name == "Chequing":
        delta = -amount      # expense reduces cash
    else:
        delta = amount     # expense increases debt

    if reverse:
        if account_name == "Chequing":
            print('test')
            delta = amount
        else:
            delta = -amount

    add_sub_money(acc, delta)

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
        transaction_type = request.transaction_type,
        account_type = request.account_type
    )
    db.add(revenue_post)

    accounts = {
        "Chequing": db.query(DbAccount).filter_by(user_id=user_id, description="Chequing").first(),
        "Visa": db.query(DbAccount).filter_by(user_id=user_id, description="Visa").first(),
        "LineOfCredit": db.query(DbAccount).filter_by(user_id=user_id, description="LineOfCredit").first(),
    }

    new_account = revenue_post.account_type
    new_category = revenue_post.category
    new_amount = revenue_post.revenue_balance

    if new_category in TRANSFER_MAP:
        new_target = TRANSFER_MAP[new_category]
        apply_transfer(new_account, new_target, new_amount, accounts, reverse=False)
        db.add(accounts[new_target])
    else:
        add_sub_money(accounts[new_account], new_amount)
    db.add(accounts[new_account])
    # if request.category == 'chequing':
    #     chequing_acc = db.query(DbAccount).filter(DbAccount.user_id == user_id,
    #                                               DbAccount.description == "Chequing").first()
    #     if not chequing_acc:
    #         raise HTTPException(status_code=404, detail="Chequing not found")
    #
    #     new_balance=chequing_acc.user_balance+ request.revenue_balance
    #     chequing_acc.user_balance=round(new_balance,2)
    #     print(chequing_acc.user_balance)
    #     db.add(chequing_acc)
    # elif request.category == 'visa':
    #     visa_acc = db.query(DbAccount).filter(DbAccount.user_id == user_id,
    #                                           DbAccount.description == "Visa").first()
    #     if not visa_acc:
    #         raise HTTPException(status_code=404, detail="Visa account not found")
    #
    #     new_balance = visa_acc.user_balance + request.revenue_balance
    #     visa_acc.user_balance = round(new_balance, 2)
    #     db.add(visa_acc)
    # elif request.category == 'lineofcredit':
    #     line_of_credit_acc = db.query(DbAccount).filter(DbAccount.user_id == user_id,
    #                                                     DbAccount.description == "LineOfCredit").first()
    #     if not line_of_credit_acc:
    #         raise HTTPException(status_code=404, detail="Visa account not found")
    #
    #     new_balance = line_of_credit_acc.user_balance + request.revenue_balance
    #     line_of_credit_acc.user_balance = round(new_balance, 2)
    #     db.add(line_of_credit_acc)

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
        transaction_type=revenue_record.transaction_type,
        account_type = revenue_record.account_type
    )
    # print(revenue_post)
    db.add(revenue_post)

    accounts = {
        "Chequing": db.query(DbAccount).filter_by(user_id=user_id, description="Chequing").first(),
        "Visa": db.query(DbAccount).filter_by(user_id=user_id, description="Visa").first(),
        "LineOfCredit": db.query(DbAccount).filter_by(user_id=user_id, description="LineOfCredit").first(),
    }

    new_account = revenue_post.account_type
    new_category = revenue_post.category
    new_amount = revenue_post.expense_balance
    if new_category in TRANSFER_MAP:
        new_target = TRANSFER_MAP[new_category]
        apply_transfer(new_account, new_target, new_amount, accounts, reverse=False)
        db.add(accounts[new_target])
    else:
        apply_normal(new_account, new_amount, accounts, reverse=False)
    db.add(accounts[new_account])
    db.commit() #'account_info':account_info
    db.refresh(revenue_post)
    return get_all_revenue(db, user_id)


def edit_revenue_record(request:EditRevenueRecord, db:Session, user_id:int):
    revenue_item = db.query(DbRevenue).filter(
        DbRevenue.revenue_id == request.id,
        DbRevenue.user_id == user_id
    ).first()
    if not revenue_item:
        raise HTTPException(status_code=404, detail="Revenue record not found")
    data=request.model_dump(exclude_unset=True)
    accounts = {
        "Chequing": db.query(DbAccount).filter_by(user_id=user_id, description="Chequing").first(),
        "Visa": db.query(DbAccount).filter_by(user_id=user_id, description="Visa").first(),
        "LineOfCredit": db.query(DbAccount).filter_by(user_id=user_id, description="LineOfCredit").first(),
    }

    old_account = revenue_item.account_type
    old_category = revenue_item.category
    old_amount = revenue_item.revenue_balance

    new_account = data['account_type']
    new_category = data['category']
    new_amount = data['revenue_balance']

    if old_category in TRANSFER_MAP:
        old_target = TRANSFER_MAP[old_category]
        apply_transfer(old_account, old_target, old_amount, accounts, reverse=True)
    else:
        apply_normal(old_account, old_amount, accounts, reverse=True)

    if new_category in TRANSFER_MAP:
        new_target = TRANSFER_MAP[new_category]
        apply_transfer(new_account, new_target, new_amount, accounts, reverse=False)
    else:
        apply_normal(new_account, new_amount, accounts, reverse=False)

    revenue_item.transaction_type = request.transaction_type
    revenue_item.description = request.description
    revenue_item.expense_balance = new_amount
    revenue_item.account_type = new_account
    revenue_item.category = new_category

    revenue_item.transaction_day = data['date'].day
    revenue_item.transaction_month = data['date'].month
    revenue_item.transaction_year = data['date'].year

    for acc in accounts.values():
        db.add(acc)

    db.add(revenue_item)

    db.commit()
    db.refresh(revenue_item)
    return get_all_revenue(db, user_id)


def delete_revenue_record(request:RecordBase, db:Session, user_id:int):
    revenue_item=db.query(DbRevenue).filter(
        DbRevenue.revenue_id == request.id,
        DbRevenue.user_id == user_id
    ).first()
    if not revenue_item:
        raise HTTPException(status_code=404, detail="Revenue record not found")

    accounts = {
        "Chequing": db.query(DbAccount).filter_by(user_id=user_id, description="Chequing").first(),
        "Visa": db.query(DbAccount).filter_by(user_id=user_id, description="Visa").first(),
        "LineOfCredit": db.query(DbAccount).filter_by(user_id=user_id, description="LineOfCredit").first(),
    }
    old_account = revenue_item.account_type
    old_category = revenue_item.category
    old_amount = revenue_item.revenue_balance

    if old_category in TRANSFER_MAP:
        old_target = TRANSFER_MAP[old_category]
        apply_transfer(old_account, old_target, old_amount, accounts, reverse=True)
        db.add(accounts[old_target])
    else:
        # print(accounts[old_account])
        apply_normal(old_account, old_amount, accounts, reverse=True)
    db.add(accounts[old_account])
    db.delete(revenue_item)
    db.commit()
    return get_all_revenue(db, user_id)