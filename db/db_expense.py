import string, random, shutil

from fastapi import HTTPException, status, Query
from decimal import Decimal
from sqlalchemy import cast, desc, Integer, select, func
from sqlalchemy.testing.pickleable import User

from routers.schemas import ExpenseBase, RecordBase, EditExpenseRecord
from sqlalchemy.orm import Session
from db.models import DbExpense, DbAccount
import datetime
from helpers import information
def apply_transfer_effect(account, amount: Decimal, direction: str):
    """
    direction:
      - 'out': money leaves this account
      - 'in': money enters this account
    """

    if account.account_kind == "asset":
        if direction == "out":
            account.user_balance = Decimal(account.user_balance) - amount
        elif direction == "in":
            account.user_balance = Decimal(account.user_balance) + amount

    elif account.account_kind == "debt":
        if direction == "out":
            # money taken from debt account increases debt
            account.user_balance = Decimal(account.user_balance) + amount
        elif direction == "in":
            # payment into debt account decreases debt
            account.user_balance = Decimal(account.user_balance) - amount
    else:
        raise HTTPException(status_code=400, detail="Unsupported account kind")
def add_expense(request: ExpenseBase, db: Session, user_id: int):
    # print(request)
    print('request', request)
    source_account = (
        db.query(DbAccount)
        .filter(
            DbAccount.user_id == user_id,
            DbAccount.account_id == request.account_id
        )
        .first()
    )

    if not source_account:
        raise HTTPException(status_code=404, detail="Source account not found")

    transaction_day = str(request.date.day)
    transaction_month = str(request.date.month)
    transaction_year = str(request.date.year)

    new_expense = DbExpense(
        description=request.description,
        expense_balance=request.expense_balance,
        transaction_day=transaction_day,
        transaction_month=transaction_month,
        transaction_year=transaction_year,
        # amount_in_dollars=request.amount_in_dollars,
        category=request.category,
        transaction_type=request.transaction_type,
        user_id=user_id,
        account_id=source_account.account_id,
        account_type=source_account.description,  # optional legacy field
        target_account_id=(
            request.target_account_id
            if request.transaction_type == "transfer"
            else None
        ),
    )

    db.add(new_expense)

    amount = Decimal(request.expense_balance)

    if request.transaction_type == "expense":
        if source_account.account_kind == "asset":
            source_account.user_balance = Decimal(source_account.user_balance) - amount
        elif source_account.account_kind == "debt":
            # spending on debt account increases debt
            source_account.user_balance = Decimal(source_account.user_balance) + amount
        else:
            raise HTTPException(status_code=400, detail="Unsupported account kind")

    elif request.transaction_type == "transfer":
        if not request.target_account_id:
            raise HTTPException(status_code=400, detail="Target account is required for transfer")

        if request.target_account_id == request.account_id:
            raise HTTPException(status_code=400, detail="Source and target account cannot be the same")

        target_account = (
            db.query(DbAccount)
            .filter(
                DbAccount.user_id == user_id,
                DbAccount.account_id == request.target_account_id
            )
            .first()
        )

        if not target_account:
            raise HTTPException(status_code=404, detail="Target account not found")

        apply_transfer_effect(source_account, amount, "out")
        apply_transfer_effect(target_account, amount, "in")

    else:
        source_account.user_balance = Decimal(source_account.user_balance) + amount

    db.commit()
    db.refresh(new_expense)

    return get_all_expense(db, user_id)

def get_all_expense(db: Session, user_id: int):
    accounts = db.query(DbAccount).filter(DbAccount.user_id == user_id).order_by(DbAccount.account_id).all()

    accounts_with_expenses=[]

    def format_account_name(name: str):
        return "Line of Credit" if name == "LineOfCredit" else name

    current_month = str(datetime.date.today().month)
    def sum_of_expenses(current_month, account_type):
        query = (select(func.sum(DbExpense.expense_balance))
                 .where(DbExpense.user_id == user_id,
                        DbExpense.transaction_month == current_month,
                        DbExpense.account_type == account_type,
                        DbExpense.transaction_type=='expense'
                        ))
        result = db.execute(query).scalar_one_or_none()
        total = result or 0
        return total

    for account in accounts:
        expenses = (db.query(DbExpense)
                .where(DbExpense.user_id == user_id, DbExpense.account_type == account.description)
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

    chequing_sum=sum_of_expenses(current_month, 'Chequing')
    visa_sum = sum_of_expenses(current_month, 'Visa')
    line_of_credit_sum = sum_of_expenses(current_month, 'LineOfCredit')

    account_info=information.collect_information(db,user_id)
    return {'message': 'Record Saved Successfully', 'expenses': accounts_with_expenses,
            'totalChequing':chequing_sum, 'totalVisa':visa_sum,
            'totalLineOfCredit':line_of_credit_sum, 'account_info':account_info}


def apply_normal(account, amount: Decimal, transaction_type: str, reverse: bool = False):
    amount = Decimal(amount)

    if transaction_type == "expense":
        if account.account_kind == "asset":
            delta = amount
        elif account.account_kind == "debt":
            delta = -amount
        else:
            raise HTTPException(status_code=400, detail="Unsupported account kind")

    elif transaction_type == "revenue":
        if account.account_kind == "asset":
            delta = -amount
        elif account.account_kind == "debt":
            delta = amount
        else:
            raise HTTPException(status_code=400, detail="Unsupported account kind")
    else:
        raise HTTPException(status_code=400, detail="Unsupported transaction type")

    if reverse:
        account.user_balance = Decimal(account.user_balance) + delta
    else:
        account.user_balance = Decimal(account.user_balance) - delta


def apply_transfer(source_account, target_account, amount: Decimal, reverse: bool = False):
    amount = Decimal(amount)

    def apply_transfer_effect(account, amt: Decimal, direction: str):
        if account.account_kind == "asset":
            if direction == "out":
                account.user_balance = Decimal(account.user_balance) - amt
            elif direction == "in":
                account.user_balance = Decimal(account.user_balance) + amt

        elif account.account_kind == "debt":
            if direction == "out":
                account.user_balance = Decimal(account.user_balance) + amt
            elif direction == "in":
                account.user_balance = Decimal(account.user_balance) - amt
        else:
            raise HTTPException(status_code=400, detail="Unsupported account kind")

    if reverse:
        apply_transfer_effect(source_account, amount, "in")
        apply_transfer_effect(target_account, amount, "out")
    else:
        apply_transfer_effect(source_account, amount, "out")
        apply_transfer_effect(target_account, amount, "in")

def copy_record(request:RecordBase, db:Session, user_id:int):
    date=datetime.date.today()
    day = date.day
    month = date.month
    year = date.year

    expense_record=db.query(DbExpense).filter(
        DbExpense.expense_id == request.id,
        DbExpense.user_id == user_id
    ).first()
    source_account = (
        db.query(DbAccount)
        .filter(
            DbAccount.user_id == user_id,
            DbAccount.account_id == expense_record.account_id
        )
        .first()
    )
    if expense_record is None:
        raise HTTPException(status_code=404, detail="Record not found")
    expense_post = DbExpense(
        description=expense_record.description,
        expense_balance=expense_record.expense_balance,
        transaction_day=day,
        transaction_month=month,
        transaction_year=year,
        # amount_in_dollars=request.amount_in_dollars,
        category=expense_record.category,
        transaction_type=expense_record.transaction_type,
        user_id=user_id,
        account_id=source_account.account_id,
        account_type=source_account.description,  # optional legacy field
        target_account_id=(
            expense_record.target_account_id
            if expense_record.transaction_type == "transfer"
            else None
        ),
    )
    # print(revenue_post)
    db.add(expense_post)
    if expense_record.transaction_type == "expense":
        if source_account.account_kind == "asset":
            source_account.user_balance = Decimal(source_account.user_balance) - expense_record.expense_balance
        elif source_account.account_kind == "debt":
            # spending on debt account increases debt
            source_account.user_balance = Decimal(source_account.user_balance) + expense_record.expense_balance
        else:
            raise HTTPException(status_code=400, detail="Unsupported account kind")

    elif expense_record.transaction_type == "transfer":
        if not expense_record.target_account_id:
            raise HTTPException(status_code=400, detail="Target account is required for transfer")

        if expense_record.target_account_id == expense_record.account_id:
            raise HTTPException(status_code=400, detail="Source and target account cannot be the same")

        target_account = (
            db.query(DbAccount)
            .filter(
                DbAccount.user_id == user_id,
                DbAccount.account_id == expense_record.target_account_id
            )
            .first()
        )

        if not target_account:
            raise HTTPException(status_code=404, detail="Target account not found")

        apply_transfer_effect(source_account, expense_record.expense_balance, "out")
        apply_transfer_effect(target_account, expense_record.expense_balance, "in")

    else:
        source_account.user_balance = Decimal(source_account.user_balance) + expense_record.expense_balance

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

    old_amount = Decimal(expense_item.expense_balance)
    old_transaction_type = expense_item.transaction_type
    old_source_account = (
        db.query(DbAccount)
        .filter(
            DbAccount.user_id == user_id,
            DbAccount.account_id == expense_item.account_id
        )
        .first()
    )
    if not old_source_account:
        raise HTTPException(status_code=404, detail="Old source account not found")
    old_target_account = None
    if expense_item.target_account_id:
        old_target_account = (
            db.query(DbAccount)
            .filter(
                DbAccount.user_id == user_id,
                DbAccount.account_id == expense_item.target_account_id
            )
            .first()
        )
    new_account_id = data.get("account_id", expense_item.account_id)
    new_target_account_id = data.get("target_account_id", expense_item.target_account_id)
    new_amount = Decimal(data.get("expense_balance", expense_item.expense_balance))
    new_transaction_type = data.get("transaction_type", expense_item.transaction_type)

    new_source_account = (
        db.query(DbAccount)
        .filter(
            DbAccount.user_id == user_id,
            DbAccount.account_id == new_account_id
        )
        .first()
    )

    if not new_source_account:
        raise HTTPException(status_code=404, detail="New source account not found")

    new_target_account = None
    if new_transaction_type == "transfer":
        if not new_target_account_id:
            raise HTTPException(status_code=400, detail="Target account is required for transfer")

        if new_target_account_id == new_account_id:
            raise HTTPException(status_code=400, detail="Source and target account cannot be the same")

        new_target_account = (
            db.query(DbAccount)
            .filter(
                DbAccount.user_id == user_id,
                DbAccount.account_id == new_target_account_id
            )
            .first()
        )

        if not new_target_account:
            raise HTTPException(status_code=404, detail="New target account not found")

    # reverse old effect
    if old_transaction_type == "transfer":
        if not old_target_account:
            raise HTTPException(status_code=400, detail="Old transfer target account not found")
        apply_transfer(old_source_account, old_target_account, old_amount, reverse=True)
    else:
        apply_normal(old_source_account, old_amount, old_transaction_type, reverse=True)

    # apply new effect
    if new_transaction_type == "transfer":
        apply_transfer(new_source_account, new_target_account, new_amount, reverse=False)
    else:
        apply_normal(new_source_account, new_amount, new_transaction_type, reverse=False)

    # update record fields
    if "transaction_type" in data:
        expense_item.transaction_type = data["transaction_type"]

    if "description" in data:
        expense_item.description = data["description"]

    expense_item.expense_balance = new_amount

    if "category" in data:
        expense_item.category = data["category"]
    elif new_transaction_type == "transfer":
        expense_item.category = "transfer"

    expense_item.account_id = new_account_id
    expense_item.target_account_id = new_target_account_id if new_transaction_type == "transfer" else None

    # optional legacy field
    expense_item.account_type = new_source_account.description

    if "date" in data:
        expense_item.transaction_day = str(data["date"].day)
        expense_item.transaction_month = str(data["date"].month)
        expense_item.transaction_year = str(data["date"].year)

    db.add(old_source_account)
    if old_target_account:
        db.add(old_target_account)

    db.add(new_source_account)
    if new_target_account:
        db.add(new_target_account)

    db.add(expense_item)
    db.commit()
    db.refresh(expense_item)
    return get_all_expense(db, user_id)


def delete_expense_record(request:RecordBase, db:Session, user_id:int):
    expense_item = (
        db.query(DbExpense)
        .filter(
            DbExpense.expense_id == request.id,
            DbExpense.user_id == user_id
        )
        .first()
    )

    if not expense_item:
        raise HTTPException(status_code=404, detail="Expense record not found")

    source_account = (
        db.query(DbAccount)
        .filter(
            DbAccount.user_id == user_id,
            DbAccount.account_id == expense_item.account_id
        )
        .first()
    )

    if not source_account:
        raise HTTPException(status_code=404, detail="Source account not found")

    target_account = None
    if expense_item.transaction_type == "transfer":
        if not expense_item.target_account_id:
            raise HTTPException(status_code=400, detail="Transfer target account is missing")

        target_account = (
            db.query(DbAccount)
            .filter(
                DbAccount.user_id == user_id,
                DbAccount.account_id == expense_item.target_account_id
            )
            .first()
        )

        if not target_account:
            raise HTTPException(status_code=404, detail="Target account not found")

    old_amount = expense_item.expense_balance
    old_transaction_type = expense_item.transaction_type

    if old_transaction_type == "transfer":
        apply_transfer(source_account, target_account, old_amount, reverse=True)
        db.add(target_account)
    else:
        apply_normal(source_account, old_amount, old_transaction_type, reverse=True)

    db.add(source_account)
    db.delete(expense_item)
    db.commit()
    return get_all_expense(db, user_id)