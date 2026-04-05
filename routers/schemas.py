from datetime import date
from typing import Optional
from decimal import Decimal



from pydantic import BaseModel, ConfigDict, EmailStr

class UserBase(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserAuth(BaseModel):
    user_id:int
    username:str
    email:str

class UserDisplay(BaseModel):
    user_id: int
    email: EmailStr

    model_config = ConfigDict(from_attributes=True)

class RevenueBase(BaseModel):
    description: str
    revenue_balance: Decimal
    date:date
    category:str
    transaction_type:str
    account_type: str

class RevenueResponse(RevenueBase):
    revenue_id: int
    user_id: int

    model_config = ConfigDict(from_attributes=True)

class EditRevenueRecord(BaseModel):
    id: int
    transaction_type: Optional[str]
    description: Optional[str]
    revenue_balance: Optional[Decimal]
    date: Optional[date]
    category: Optional[str]
    account_type: Optional[str]

class ExpenseBase(BaseModel):
    description: str
    expense_balance: Decimal
    date: date
    category: str
    account_type: str
    transaction_type: str

class ExpenseResponse(ExpenseBase):
    expense_id: int
    user_id: int

    model_config = ConfigDict(from_attributes=True)

class EditExpenseRecord(BaseModel):
    id: int
    transaction_type: Optional[str]
    description: Optional[str]
    expense_balance: Optional[Decimal]
    date: Optional[date]
    account_type: Optional[str]
    category: Optional[str]

    model_config = ConfigDict(from_attributes=True)

class AccountBase(BaseModel):
    description: str
    user_balance: Decimal

class AccountResponse(AccountBase):
    account_id: int
    user_id: int

    model_config = ConfigDict(from_attributes=True)

class RecordBase(BaseModel):
    id:int
    type:str

class Analytics(BaseModel):
    account_type:str
    account_type_second: Optional[str]=None

class SearchRecord(BaseModel):
    description: str

class AgentDisplay(BaseModel):
    transaction_type:str
    expense_balance:Decimal
    description:str
    date:date
    account_type:str
    category:str

class AgentRequestBase(BaseModel):
    description: str

class CategoryBase(BaseModel):
    description: str

class CategoryDisplay(BaseModel):
    category_id:int
    description: str
    category_name: str

    model_config = ConfigDict(from_attributes=True)

class CategoryRecordBase(BaseModel):
    category_id:int