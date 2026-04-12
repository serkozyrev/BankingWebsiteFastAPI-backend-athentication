from fastapi import HTTPException
from sqlalchemy import desc,cast, Integer,func, select

from routers.schemas import RecordBase, SearchRecord
from sqlalchemy.orm import Session
from db.models import DbAccount, DbExpense
import datetime

def collect_information(db:Session, user_id:int):
    accounts = db.query(DbAccount).filter(DbAccount.user_id == user_id).order_by(DbAccount.account_id).all()
    accounts_list = [
        {
            'id': account.account_id,
            'description': "Line of Credit" if account.description == "LineOfCredit" else account.description,
            'account_kind': account.account_kind,
            'amount': account.user_balance
        }
        for account in accounts
    ]

    return {"accounts": accounts_list}

def get_by_id_info(request:RecordBase, db:Session, user_id:int):

    transaction_by_id=db.query(DbExpense).filter(DbExpense.expense_id==request.id, DbExpense.user_id==user_id).first()
    if not transaction_by_id:
        raise HTTPException(status_code=404, detail="Revenue not found")
    expense_item = {
            'id': transaction_by_id.expense_id,
            'description': transaction_by_id.description,
            'amount': transaction_by_id.expense_balance,
            'day': transaction_by_id.transaction_day,
            'month': transaction_by_id.transaction_month,
            'year': transaction_by_id.transaction_year,
            'amountindollars': transaction_by_id.amount_in_dollars,
            'account_id': transaction_by_id.account_id,
            'category': transaction_by_id.category,
            'type': transaction_by_id.transaction_type,
            'accountType': transaction_by_id.account_type,
            'transactionById': transaction_by_id.target_account_id
        }

    return {'expense': expense_item}

def search(request:SearchRecord,db:Session, user_id:int):
    accounts = db.query(DbAccount).filter(DbAccount.user_id == user_id).order_by(DbAccount.account_id).all()

    accounts_with_expenses = []

    def format_account_name(name: str):
        return "Line of Credit" if name == "LineOfCredit" else name

    current_month = str(datetime.date.today().month)
    def sum_of_expenses(current_month, account_type):
        query = (select(func.sum(DbExpense.expense_balance))
                 .where(DbExpense.user_id == user_id,
                        DbExpense.transaction_month == current_month,
                        DbExpense.account_type == account_type
                        ))
        result = db.execute(query).scalar_one_or_none()
        total = result or 0
        return total

    for account in accounts:
        expenses = (db.query(DbExpense)
                .where(DbExpense.user_id == user_id,
                       func.lower(DbExpense.description).like(f"%{request.description.lower()}%"),
                       DbExpense.account_type == account.description)
                 .order_by(
                    desc(cast(DbExpense.transaction_year, Integer)),
                    desc(cast(DbExpense.transaction_month, Integer)),
                    desc(cast(DbExpense.transaction_day, Integer))
                ).all())
        expenses_list = [
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
            for expense in expenses
        ]

        accounts_with_expenses.append({
            "id": account.account_id,
            "description": format_account_name(account.description),
            "amount": account.user_balance,
            "currentMonthTotal": sum_of_expenses(current_month, account.description),
            "expenses": expenses_list
        })
    return {'searchExpenses':accounts_with_expenses}
