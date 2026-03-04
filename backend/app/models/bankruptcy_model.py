from sqlalchemy import Column, Integer, Float, String, Date
from app.database import Base

class BankruptcyRisk(Base):
    __tablename__ = "bankruptcy_risk"

    id = Column(Integer, primary_key=True, index=True)
    month = Column(Date, unique=True)

    probability = Column(Float)     # 0 → 1
    risk_level = Column(String)     # LOW / MEDIUM / HIGH / EXTREME
    survival_months = Column(Integer)