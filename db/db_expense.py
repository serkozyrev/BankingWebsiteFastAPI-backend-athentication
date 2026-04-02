import string, random, shutil

from fastapi import HTTPException, status
from decimal import Decimal
from sqlalchemy import cast, desc, Integer, select, func
from sqlalchemy.testing.pickleable import User

from routers.schemas import ExpenseBase, RecordBase, EditExpenseRecord
from sqlalchemy.orm import Session
from db.models import DbExpense, DbAccount
import datetime
from helpers import information

def add_expense(request: ExpenseBase, db: Session, user_id: int):
    # print(request)

    request_date=request.date
    day=request_date.day
    month=request_date.month
    year=request_date.year

    expense_post=DbExpense(
        user_id=user_id,
        description=request.description,
        expense_balance = request.expense_balance,
        transaction_day = day,
        transaction_month = month,
        transaction_year = year,
        category = request.category,
        transaction_type = request.transaction_type,
        account_type=request.account_type
    )
    db.add(expense_post)
    accounts = {
        "Chequing": db.query(DbAccount).filter_by(user_id=user_id, description="Chequing").first(),
        "Visa": db.query(DbAccount).filter_by(user_id=user_id, description="Visa").first(),
        "LineOfCredit": db.query(DbAccount).filter_by(user_id=user_id, description="LineOfCredit").first(),
    }

    new_account = expense_post.account_type
    new_category = expense_post.category
    new_amount = expense_post.expense_balance

    if new_category in TRANSFER_MAP:
        new_target = TRANSFER_MAP[new_category]
        apply_transfer(new_account, new_target, new_amount, accounts, reverse=False)
        db.add(accounts[new_target])
    else:
        add_sub_money(accounts[new_account], new_amount)
    db.add(accounts[new_account])

    db.commit()
    db.refresh(expense_post) #'account_info':account_info
    return get_all_expense(db, user_id)

def get_all_expense(db: Session, user_id: int):
    expenses_visa = (db.query(DbExpense).
                     where(DbExpense.user_id == user_id,DbExpense.account_type=='Visa')
                     .order_by(
                        desc(cast(DbExpense.transaction_year, Integer)),
                        desc(cast(DbExpense.transaction_month, Integer)),
                        desc(cast(DbExpense.transaction_day,Integer))
                    ).all())
    expenses_chequing_line_of_credit = (db.query(DbExpense).
                     filter(DbExpense.user_id == user_id,DbExpense.account_type.in_(['Chequing','LineOfCredit']))
                     .order_by(
                        desc(cast(DbExpense.transaction_year, Integer)),
                        desc(cast(DbExpense.transaction_month, Integer)),
                        desc(cast(DbExpense.transaction_day, Integer))
                    ).all())
    expenses_list_visa=[
        {
            'id': expense.expense_id,
            'description': expense.description,
            'amount': expense.expense_balance,
            'day': expense.transaction_day,
            'month': expense.transaction_month,
            'year': expense.transaction_year,
            'category':expense.category,
            'accountType':expense.account_type,
            'type':expense.transaction_type,
            'amountindollar':expense.amount_in_dollars
        }
        for expense in expenses_visa
    ]
    expenses_list_chequing_line_of_credit = [
        {
            'id': expense.expense_id,
            'description': expense.description,
            'amount': expense.expense_balance,
            'day': expense.transaction_day,
            'month': expense.transaction_month,
            'year': expense.transaction_year,
            'category': expense.category,
            'accountType': expense.account_type,
            'type': expense.transaction_type,
            'amountindollar': expense.amount_in_dollars
        }
        for expense in expenses_chequing_line_of_credit
    ]
    # print(expenses_list_chequing_line_of_credit)
    current_month=str(datetime.date.today().month)
    def sum_of_expenses(current_month, account_type):
        query = select(func.sum(DbExpense.expense_balance)).where(DbExpense.user_id == user_id,
            DbExpense.transaction_month == current_month,
            DbExpense.account_type == account_type
        )

        result = db.execute(query).scalar_one_or_none()
        total = result or 0
        return total

    chequing_sum=sum_of_expenses(current_month, 'Chequing')
    visa_sum = sum_of_expenses(current_month, 'Visa')
    line_of_credit_sum = sum_of_expenses(current_month, 'LineOfCredit')

    # print(expenses_list_visa)
    account_info=information.collect_information(db,user_id)
    return {'message': 'Record Saved Successfully', 'expensesVisa':expenses_list_visa,
            'expensesChequingLineOfCredit': expenses_list_chequing_line_of_credit,
            'totalChequing':chequing_sum, 'totalVisa':visa_sum,
            'totalLineOfCredit':line_of_credit_sum, 'account_info':account_info}


TRANSFER_MAP = {
    "transferToChequing": "Chequing",
    "transferToVisa": "Visa",
    "transferToLineOfCredit": "LineOfCredit",
}

def add_sub_money(account, amount):
    account.user_balance = round(account.user_balance + amount, 2)


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

def copy_record(request:RecordBase, db:Session, user_id:int):
    date=datetime.date.today()
    day = date.day
    month = date.month
    year = date.year

    expense_record=db.query(DbExpense).filter(
        DbExpense.expense_id == request.id,
        DbExpense.user_id == user_id
    ).first()
    if expense_record is None:
        raise HTTPException(status_code=404, detail="Record not found")
    expense_post = DbExpense(
        user_id=user_id,
        description=expense_record.description,
        expense_balance=expense_record.expense_balance,
        transaction_day=day,
        transaction_month=month,
        transaction_year=year,
        category=expense_record.category,
        transaction_type=expense_record.transaction_type,
        account_type=expense_record.account_type
    )
    # print(revenue_post)
    db.add(expense_post)

    accounts = {
        "Chequing": db.query(DbAccount).filter_by(user_id=user_id, description="Chequing").first(),
        "Visa": db.query(DbAccount).filter_by(user_id=user_id, description="Visa").first(),
        "LineOfCredit": db.query(DbAccount).filter_by(user_id=user_id, description="LineOfCredit").first(),
    }

    new_account = expense_post.account_type
    new_category = expense_post.category
    new_amount = expense_post.expense_balance

    if new_category in TRANSFER_MAP:
        new_target = TRANSFER_MAP[new_category]
        apply_transfer(new_account, new_target, new_amount, accounts, reverse=False)
        db.add(accounts[new_target])
    else:
        apply_normal(new_account, new_amount, accounts, reverse=False)

    db.add(accounts[new_account])
    db.commit() #'account_info':account_info
    db.refresh(expense_post)
    return get_all_expense(db, user_id)

def edit_expense_record(request:EditExpenseRecord, db:Session, user_id:int):
    expense_item = db.query(DbExpense).filter(
        DbExpense.expense_id == request.id,
        DbExpense.user_id == user_id
    ).first()

    if not expense_item:
        raise HTTPException(status_code=404, detail="Expense record not found")
    data=request.model_dump(exclude_unset=True)
    # accounts
    accounts = {
        "Chequing": db.query(DbAccount).filter_by(user_id=user_id, description="Chequing").first(),
        "Visa": db.query(DbAccount).filter_by(user_id=user_id, description="Visa").first(),
        "LineOfCredit": db.query(DbAccount).filter_by(user_id=user_id, description="LineOfCredit").first(),
    }

    old_account = expense_item.account_type
    old_category = expense_item.category
    old_amount = expense_item.expense_balance

    new_account = data['account_type']
    new_category = data['category']
    new_amount = data['expense_balance']

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

    expense_item.transaction_type = request.transaction_type
    expense_item.description = request.description
    expense_item.expense_balance = new_amount
    expense_item.account_type = new_account
    expense_item.category = new_category

    expense_item.transaction_day = data['date'].day
    expense_item.transaction_month = data['date'].month
    expense_item.transaction_year = data['date'].year

    for acc in accounts.values():
        db.add(acc)

    db.add(expense_item)
    db.commit()
    db.refresh(expense_item)
    return get_all_expense(db, user_id)


def delete_expense_record(request:RecordBase, db:Session, user_id:int):
    expense_item = db.query(DbExpense).filter(
        DbExpense.expense_id == request.id,
        DbExpense.user_id == user_id
    ).first()
    if not expense_item:
        raise HTTPException(status_code=404, detail="Expense record not found")

    accounts = {
        "Chequing": db.query(DbAccount).filter_by(user_id=user_id, description="Chequing").first(),
        "Visa": db.query(DbAccount).filter_by(user_id=user_id, description="Visa").first(),
        "LineOfCredit": db.query(DbAccount).filter_by(user_id=user_id, description="LineOfCredit").first(),
    }
    old_account = expense_item.account_type
    old_category = expense_item.category
    old_amount = expense_item.expense_balance

    if old_category in TRANSFER_MAP:
        old_target = TRANSFER_MAP[old_category]
        apply_transfer(old_account, old_target, old_amount, accounts, reverse=True)
        db.add(accounts[old_target])
    else:
        # print(accounts[old_account])
        apply_normal(old_account, old_amount, accounts, reverse=True)
    # if expense_item.account_type == 'Chequing':
    #     db.add(accounts[old_account])
    # elif expense_item.account_type == 'LineOfCredit':
    #     db.add(line_of_credit_acc)
    # else:
    #     db.add(visa_acc)
    db.add(accounts[old_account])
    db.delete(expense_item)
    db.commit()
    return get_all_expense(db, user_id)