import string, random, shutil
from typing import Optional

from fastapi import HTTPException, status
from decimal import Decimal
from sqlalchemy import cast, desc, Integer, select, func

from routers.schemas import Analytics
from sqlalchemy.orm import Session
from db.models import DbExpense, DbAccount, DbCategories
import datetime

def analytics_expense(db: Session, user_id:int):
    accounts = (
        db.query(DbAccount)
        .filter(DbAccount.user_id == user_id)
        .order_by(DbAccount.account_id)
        .all()
    )

    categories = db.query(DbCategories).filter(DbCategories.user_id == user_id).all()

    category_titles = {
        category.category_name: category.description
        for category in categories
    }
    category_titles["salary"] = "Salary"

    current_month = str(datetime.date.today().month)

    expenses_analysis = []

    for account in accounts:
        info_list = []
        yearly_summary = []

        records = (
            db.query(DbExpense)
            .filter(
                DbExpense.user_id == user_id,
                DbExpense.account_id == account.account_id,
                DbExpense.transaction_month == current_month
            )
            .all()
        )

        current_month_grouped = {}

        for expense in records:
            if expense.transaction_type == "transfer" and expense.target_account_id:
                target_account = (
                    db.query(DbAccount)
                    .filter(
                        DbAccount.user_id == user_id,
                        DbAccount.account_id == expense.target_account_id
                    )
                    .first()
                )

                title = (
                    f"Transfer to {target_account.description}"
                    if target_account
                    else "Transfer"
                )
                group_key = f"transfer-{expense.target_account_id}"
                raw_type = "transfer"
            else:
                title = category_titles.get(expense.category, expense.category)
                group_key = expense.category
                raw_type = expense.category

            if group_key not in current_month_grouped:
                current_month_grouped[group_key] = {
                    "title": title,
                    "amount": 0,
                    "year": expense.transaction_year,
                    "type": raw_type,
                }

            current_month_grouped[group_key]["amount"] += float(expense.expense_balance)

        for value in current_month_grouped.values():
            value["amount"] = round(value["amount"], 2)
            info_list.append(value)

        all_records = (
            db.query(DbExpense)
            .filter(
                DbExpense.user_id == user_id,
                DbExpense.account_id == account.account_id
            )
            .all()
        )

        yearly_grouped = {}

        for expense in all_records:
            if expense.transaction_type == "transfer" and expense.target_account_id:
                target_account = (
                    db.query(DbAccount)
                    .filter(
                        DbAccount.user_id == user_id,
                        DbAccount.account_id == expense.target_account_id
                    )
                    .first()
                )

                title = (
                    f"Transfer to {target_account.description}"
                    if target_account
                    else "Transfer"
                )
                group_key = f"transfer-{expense.target_account_id}-{expense.transaction_month}-{expense.transaction_year}"
            else:
                title = category_titles.get(expense.category, expense.category)
                group_key = f"{expense.category}-{expense.transaction_month}-{expense.transaction_year}"

            if group_key not in yearly_grouped:
                yearly_grouped[group_key] = {
                    "title": title,
                    "amount": 0,
                    "month": expense.transaction_month,
                    "year": expense.transaction_year,
                }

            yearly_grouped[group_key]["amount"] += float(expense.expense_balance)

        yearly_summary = [
            {
                "title": item["title"],
                "amount": round(item["amount"], 2),
                "month": item["month"],
                "year": item["year"],
            }
            for item in yearly_grouped.values()
        ]

        for record in info_list:
            for item in yearly_summary:
                if record["title"] == item["title"]:
                    record.setdefault("summary", []).append(item)

        expenses_analysis.append({
            "id": account.account_id,
            "description": account.description,
            "expenses_info": info_list
        })
    return {'info':expenses_analysis}
