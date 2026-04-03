import string, random, shutil
from typing import Optional

from fastapi import HTTPException, status
from decimal import Decimal
from sqlalchemy import cast, desc, Integer, select, func

from routers.schemas import Analytics
from sqlalchemy.orm import Session
from db.models import DbExpense, DbAccount, DbRevenue
import datetime

def analytics_expense(db: Session, user_id:int, account_types:list[str]):
    info_list=[]
    yearly_summary = []
    current_month=str(datetime.date.today().month)
    # category_list = ['grocery', 'transferToVisa', 'utilitiesPayment', 'otherPayment', 'transferLineOfCredit', 'transferToChequing', 'medicine']
    category_titles = {
        "utilitiesPayment": "Utilities",
        "otherPayment": "Other Payment",
        "medicine": "Medicine",
        "grocery": "Grocery",
    }

    information = (
        db.query(
            DbExpense.category,
            func.sum(DbExpense.expense_balance),
            DbExpense.transaction_year
        )
        .filter(
            DbExpense.user_id == user_id,
            DbExpense.transaction_month == current_month,
            DbExpense.account_type.in_(account_types)
        )
        .group_by(
            DbExpense.transaction_month,
            DbExpense.category,
            DbExpense.transaction_year
        )
        .all()
    )
    for category, amount, year in information:
        info_list.append({
            "title": category_titles.get(category, category),
            "amount": round(amount, 2),
            "year": year,
            "type": category
        })


    category_summary = (
        db.query(
            DbExpense.category,
            func.sum(DbExpense.expense_balance),
            DbExpense.transaction_month,
            DbExpense.transaction_year
        )
        .filter(
            DbExpense.user_id == user_id,
            DbExpense.account_type.in_(account_types)
        )
        .group_by(
            DbExpense.transaction_month,
            DbExpense.category,
            DbExpense.transaction_year
        )
        .all()
    )

    for title, amount, month, year in category_summary:
        yearly_summary.append({
            "title": title,
            "amount": round(amount, 2),
            "month": month,
            "year": year
        })
    for record in info_list:
        for item in yearly_summary:
            if record["type"] == item["title"]:
                record.setdefault("summary", []).append(item)
    return {'info':info_list}

def analytics_revenue(db: Session, user_id:int, account_types:list[str]):
    info_list=[]
    yearly_summary = []
    current_month=str(datetime.date.today().month)
    # category_list = ['grocery', 'transferToVisa', 'utilitiesPayment', 'otherPayment', 'transferLineOfCredit', 'transferToChequing', 'medicine']
    category_titles = {
        "transferToChequing": "Transfer to Cheching",
        "transferToVisa": "Transfer to Visa",
        "transferToLineOfCredit": "Transfer to Line of Credit",
        "salary": "Salary",
    }

    information = (
        db.query(
            DbRevenue.category,
            func.sum(DbRevenue.revenue_balance),
            DbRevenue.transaction_year
        )
        .filter(
            DbRevenue.user_id == user_id,
            DbRevenue.transaction_month == current_month,
            DbRevenue.account_type.in_(account_types)
        )
        .group_by(
            DbRevenue.transaction_month,
            DbRevenue.category,
            DbRevenue.transaction_year
        )
        .all()
    )
    print('information_revenue',information)
    for category, amount, year in information:
        info_list.append({
            "title": category_titles.get(category, category),
            "amount": round(amount, 2),
            "year": year,
            "type": category
        })


    category_summary = (
        db.query(
            DbRevenue.category,
            func.sum(DbRevenue.revenue_balance),
            DbRevenue.transaction_month,
            DbRevenue.transaction_year
        )
        .filter(
            DbRevenue.user_id == user_id,
            DbRevenue.account_type.in_(account_types)
        )
        .group_by(
            DbRevenue.transaction_month,
            DbRevenue.category,
            DbRevenue.transaction_year
        )
        .all()
    )

    for title, amount, month, year in category_summary:
        yearly_summary.append({
            "title": title,
            "amount": round(amount, 2),
            "month": month,
            "year": year
        })
    for record in info_list:
        for item in yearly_summary:
            if record["type"] == item["title"]:
                record.setdefault("summary", []).append(item)
    return {'info':info_list}
