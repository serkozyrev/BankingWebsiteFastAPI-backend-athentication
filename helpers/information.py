from sqlalchemy import desc,cast, Integer,func

from routers.schemas import RecordBase, SearchRecord
from sqlalchemy.orm import Session
from db.models import DbRevenue, DbAccount, DbExpense
import datetime

def collect_information(db:Session, user_id:int):
    visa = db.query(DbAccount).filter(DbAccount.user_id == user_id,DbAccount.description == 'Visa').first()

    chequing = db.query(DbAccount).filter(DbAccount.user_id == user_id,DbAccount.description == 'Chequing').first()

    line_of_credit = db.query(DbAccount).filter(DbAccount.user_id == user_id,DbAccount.description == 'LineOfCredit').first()

    return {"chequing": chequing.user_balance, "line_of_credit": line_of_credit.user_balance, "visa": visa.user_balance}

def get_by_id_info(request:RecordBase, db:Session):
    if request.type =='revenue':
        transaction_by_id=db.query(DbRevenue).filter(DbRevenue.revenue_id==request.id).first()
        revenues_item = {
                'id': transaction_by_id.revenue_id,
                'description': transaction_by_id.description,
                'amount': transaction_by_id.revenue_balance,
                'day': transaction_by_id.transaction_day,
                'month': transaction_by_id.transaction_month,
                'year': transaction_by_id.transaction_year,
                'category': transaction_by_id.category,
                'type': request.type,
                'accountType': transaction_by_id.account_type
            }

        return {'revenue': revenues_item}
    elif request.type =='expense':
        transaction_by_id=db.query(DbExpense).filter(DbExpense.expense_id==request.id).first()
        expense_item = {
                'id': transaction_by_id.expense_id,
                'description': transaction_by_id.description,
                'amount': transaction_by_id.expense_balance,
                'day': transaction_by_id.transaction_day,
                'month': transaction_by_id.transaction_month,
                'year': transaction_by_id.transaction_year,
                'amountindollars': transaction_by_id.amount_in_dollars,
                'category': transaction_by_id.category,
                'type': request.type,
                'accountType': transaction_by_id.account_type
            }

        return {'expense': expense_item}

def search(request:SearchRecord,db:Session):
    result = (
        db.query(DbExpense)
        .filter(
            func.lower(DbExpense.description).like(f"%{request.description.lower()}%")
        )
        .order_by(
            desc(cast(DbExpense.transaction_year, Integer)),
            desc(cast(DbExpense.transaction_month, Integer)),
            desc(cast(DbExpense.transaction_day, Integer)),
        )
        .all()
    )

    expenses_list = []
    expenses_list_visa = []
    for record in result:
        if record.account_type == 'Visa':
            new_expense_visa={
                'id': record.expense_id, 'description': record.description, 'amount': record.expense_balance,
                'day': record.transaction_day, 'month': record.transaction_month, 'year': record.transaction_year,
                'amountindollars': record.amount_in_dollars, 'category': record.category, 'type': record.transaction_type
            }
            expenses_list_visa.append(new_expense_visa)
        else:
            new_expense={
                'id': record.expense_id, 'description': record.description, 'amount': record.expense_balance,
                'day': record.transaction_day, 'month': record.transaction_month, 'year': record.transaction_year,
                'amountindollars': record.amount_in_dollars, 'category': record.category, 'type': record.transaction_type
            }
            expenses_list.append(new_expense)

    return {'expensesListVisa': expenses_list_visa, 'expensesList': expenses_list}
