import os
from datetime import date
# from openai import OpenAI, AsyncOpenAI
from google import genai
from google.genai import types

import json
from dotenv import load_dotenv
load_dotenv()
# client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
today_str = date.today().isoformat()
SYSTEM_PROMPT = f"""
You are a helper for home accounting software.
Your responsibility is to translate user request into JSON.
Response only in JSON format without additional explanations. Today's date is {today_str}.
if user types something like "today", "today's date", "today date", use {today_str} exactly.
There will be two transaction types income and expense.
Transfers of money between accounts will be a part of transfer type and have categories 
like transferToVisa, transferToLineOfCredit or transferToChequing, grocery, utilitiesPayment, otherPayment, medicine. The system has three account types 
like Chequing, Visa and LineOfCredit. if you see something like salary, hst refund, wage or deposit, put revenue as transaction type.
Date should come in the format yyyy-mm-dd. Description field can be generate from the user input. If you see extra words convert them in description if needed or remove.
If the language is Russian, translate it in terms of financial terms based on previous requirements for JSON format.

Format:
{{  
  "transaction_type": "revenue" | "transfer" | "expense",
  "description": string | null,
  "date": date | null,
  "category": string | null,
  "expense_balance": number | null,
  "account_type":string | null
}}
"""
from routers.schemas import RevenueBase, RecordBase, EditRevenueRecord, AgentRequestBase
from sqlalchemy.orm import Session
from db.models import DbRevenue, DbAccount
import datetime
from helpers import information


async def parse_entry_with_ai(request: AgentRequestBase, db:Session):
    print(request.description)
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=request.description,
        config=types.GenerateContentConfig(
            system_instruction = SYSTEM_PROMPT,
            response_mime_type="application/json",
            )
    )
    # response = await client.responses.create(
    #     model="gpt-5.4",
    #     input=[
    #         {"role": "system", "content": SYSTEM_PROMPT},
    #         {"role": "user", "content": request.description}
    #     ]
    # )
    #
    raw_text = response.text
    parsed = json.loads(raw_text)
    print(parsed)

    return parsed