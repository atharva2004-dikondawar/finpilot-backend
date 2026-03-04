from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Date
from app.database import Base
from sqlalchemy.sql import func

class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    account_type = Column(String)   
    
class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    description = Column(String, nullable=False)
    amount = Column(Float, nullable=False)

    debit_account_id = Column(Integer, ForeignKey("accounts.id"))
    credit_account_id = Column(Integer, ForeignKey("accounts.id"))

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
class FinancialSnapshot(Base):
    __tablename__ = "financial_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    month = Column(Date, unique=True)
    total_revenue = Column(Float)
    total_expense = Column(Float)
    profit = Column(Float)
    cash_balance = Column(Float)
