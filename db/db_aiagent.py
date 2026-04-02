import os
import string, random, shutil

from fastapi import HTTPException, status
from decimal import Decimal
from sqlalchemy import cast, desc, Integer
from openai import OpenAI
import json
from dotenv import load_dotenv
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
SYSTEM_PROMPT = """
You are a helper for home accounting software.
Your responsibility is to translate user request into JSON.
Response only in JSON format without additional explanations.
There will be two transaction types income and expense.
Transfers of money between accounts will be a part of income type and have categories 
like transferToVisa, transferToLineOfCredit or transferToChequing. The system has three account types 
like Chequing, Visa and LineOfCredit. Date should come in the format yyyy-mm-dd. If the language is Russian, 
translate it in terms of financial terms.

Format:
{
  "intent": "create_transaction" | "ask_report" | "update_transaction",
  "transaction_type": "income" | "expense" | "transfer" | null,
  "amount": number | null,
  "account_type":string | null,
  "category": string | null,
  "description": string | null,
  "date": date | null
}
"""
from routers.schemas import RevenueBase, RecordBase, EditRevenueRecord, AgentRequestBase
from sqlalchemy.orm import Session
from db.models import DbRevenue, DbAccount
import datetime
from helpers import information


def parse_entry_with_ai(request: AgentRequestBase, db:Session, user_id:int):
    print(request)
    response = client.responses.create(
        model="gpt-5.4",
        input=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": request.description}
        ]
    )

    raw_text = response.output_text
    print(raw_text)