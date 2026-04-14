import os
from datetime import date
# from openai import OpenAI, AsyncOpenAI
from google import genai
from google.genai import types
from db.models import DbCategories, DbAccount
import json
from dotenv import load_dotenv
load_dotenv()
# client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
today_str = date.today().isoformat()

from routers.schemas import RecordBase, AgentRequestBase
from sqlalchemy.orm import Session


async def parse_entry_with_ai(request: AgentRequestBase, db:Session, user_id:int):

    categories = db.query(DbCategories).filter(DbCategories.user_id == user_id).all()
    category_titles = []

    for category in categories:
        category_titles.append(category.category_name)

    accounts_list=(
        db.query(DbAccount)
        .filter(
            DbAccount.user_id == user_id
        )
        .all()
    )
    accounts = []
    for account in accounts_list:
        accounts.append({
            "id": account.account_id,
            "description": account.description,
            "account_kind": account.account_kind
        })



    SYSTEM_PROMPT = f"""
    You are a helper for home accounting software.
    Your responsibility is to translate user input into structured JSON.
    
    Response ONLY in valid JSON format. Do not include explanations.
    
    Today's date is {today_str}.
    If user mentions "today", "today's date", or similar, use {today_str} exactly.
    
    ---
    
    SYSTEM RULES:
    
    1. Transaction types:
       - "expense"
       - "transfer"
       - "revenue" (use instead of "deposit")
    
    2. Detect transaction type:
       - If user mentions salary, wage, income, refund  or anything that can be treated as adding money → "revenue"
       - If user mentions sending/moving money between accounts → "transfer"
       - Otherwise → "expense"
    
    3. Accounts:
       - Accounts are dynamic. DO NOT assume fixed names.
       - Use provided account list: ${accounts}
       - Match user text to account description → return corresponding account_id
       - account_type should be the account description (optional helper field)
    
    4. Transfers:
       - category MUST be "transfer"
       - MUST include:
         - account_id → source account
         - target_account_id → destination account
       - If destination account is not clear, set target_account_id = null
    
    5. Non-transfer:
       - DO NOT include target_account_id
       - category should come from ${category_titles}
    
    6. Amount:
       - Extract numeric value → expense_balance
       - Always positive number
    
    7. Date:
       - Format: YYYY-MM-DD
       - Use {today_str} if not provided or if user says "today"
    
    8. Description:
       - Generate short clean description based on input
       - Remove unnecessary words
    
    9. Language:
       - If input is Russian, translate into English financial terms
    
    ---
    
    OUTPUT FORMAT:
    
    {{
      "transaction_type": "expense" | "transfer" | "revenue",
      "description": string | null,
      "date": "YYYY-MM-DD",
      "category": string | null,
      "expense_balance": number | null,
      "account_id": integer | null,
      "target_account_id": integer | null,
      "account_type": string | null
    }}
    """

    # print(request.description)
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=request.description,
        config=types.GenerateContentConfig(
            system_instruction = SYSTEM_PROMPT,
            response_mime_type="application/json",
            )
    )
    raw_text = response.text
    parsed = json.loads(raw_text)
    print(parsed)

    return parsed