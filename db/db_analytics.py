import string, random, shutil
from typing import Optional

from fastapi import HTTPException, status
from decimal import Decimal
from sqlalchemy import cast, desc, Integer, select, func

from routers.schemas import Analytics
from sqlalchemy.orm import Session
from db.models import DbExpense, DbAccount, DbRevenue, DbCategories
import datetime

def analytics_expense(db: Session, user_id:int, account_types:list[str]):
    categories = db.query(DbCategories).filter(DbCategories.user_id == user_id).all()
    category_titles ={
        **{
        category.category_name:category.description
        for category in categories
        },
        "transferLineOfCredit": "Transfer to Line of Credit",
        "transferToChequing":"Transfer to Chequing",
        "transferToVisa":"Transfer to Visa",
    }
    print(category_titles)
    info_list=[]
    yearly_summary = []
    current_month=str(datetime.date.today().month)
    # category_list = ['grocery', 'transferToVisa', 'utilitiesPayment', 'otherPayment', 'transferLineOfCredit', 'transferToChequing', 'medicine']
    # category_titles = {
    #     "transferLineOfCredit":"Transfer to Line of Credit",
    #     "transferToChequing":"Transfer to Chequing",
    #     "transferToVisa":"Transfer to Visa",
    #     "utilitiesPayment": "Utilities",
    #     "otherPayment": "Other Payment",
    #     "medicine": "Medicine",
    #     "grocery": "Grocery",
    #     "condoFee":"Condo Fee",
    #     "propertyTax": "Property Tax",
    #     "enercare":"Enercare",
    #     "enbridge":"Enbridge",
    #     "hydro":"Hydro",
    #     "water":"Water",
    #     "carInsurance":"Car Insurance",
    #     "cellPhoneExpenses":"Cell Phone Expenses",
    #     "rrsp":"RRSP",
    #     "bankCharges":"Bank Charges",
    #     "officeSupplies":"Office Supplies",
    #     "homeExpenses":"Home Expenses",
    #     "catExpenses":"Cat Expenses",
    #     "computerExpenses":"Computer Expenses",
    #     "clothes": "Clothes"
    # }

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
