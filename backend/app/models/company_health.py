from sqlalchemy import Column, Integer, Float, String, Date
from app.database import Base


class CompanyHealth(Base):
    __tablename__ = "company_health"

    id = Column(Integer, primary_key=True, index=True)
    month = Column(Date, unique=True)

    health_score = Column(Float)
    status = Column(String)
    risk_level = Column(String)