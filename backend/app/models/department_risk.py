from sqlalchemy import Column, Integer, Float, String, ForeignKey
from app.database import Base


class DepartmentRisk(Base):
    __tablename__ = "department_risk"

    id = Column(Integer, primary_key=True, index=True)
    department_id = Column(Integer, ForeignKey("departments.id"))

    total_expense = Column(Float)
    fraud_transactions = Column(Integer)
    fraud_ratio = Column(Float)

    risk_score = Column(Float)
    risk_level = Column(String)