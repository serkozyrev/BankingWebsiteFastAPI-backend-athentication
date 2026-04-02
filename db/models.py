from sqlalchemy.orm import relationship

from sqlalchemy import Column, String, ForeignKey, Numeric
from sqlalchemy.sql.sqltypes import Integer, Boolean, DateTime

from db.database import Base

class DbUser(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    password = Column(String, nullable=False)

    accounts = relationship("DbAccount", back_populates="user", cascade="all, delete-orphan")
    expenses = relationship("DbExpense", back_populates="user", cascade="all, delete-orphan")
    revenues = relationship("DbRevenue", back_populates="user", cascade="all, delete-orphan")

class DbAccount(Base):
    __tablename__ = "account"
    account_id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    user_balance = Column(Numeric(12, 2), nullable=False, default=0)
    description = Column(String)
    user = relationship("DbUser", back_populates="accounts")


class DbExpense(Base):
    __tablename__ = "expense"
    expense_id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    description = Column(String)
    expense_balance = Column(Numeric(12, 2), nullable=False)
    transaction_day = Column(String)
    transaction_month = Column(String)
    transaction_year = Column(String)
    amount_in_dollars = Column(Numeric(12,2))
    category = Column(String)
    transaction_type = Column(String)
    account_type = Column(String)
    user = relationship("DbUser", back_populates="expenses")

class DbRevenue(Base):
    __tablename__ = "revenue"
    revenue_id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    description = Column(String, nullable=False)
    revenue_balance = Column(Numeric(12,2), nullable=False)
    transaction_day = Column(String)
    transaction_month = Column(String)
    transaction_year = Column(String)
    category = Column(String)
    transaction_type = Column(String)
    account_type = Column(String)
    user = relationship("DbUser", back_populates="revenues")
