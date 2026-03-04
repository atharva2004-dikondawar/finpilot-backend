from sqlalchemy import Column, Integer, Float, String, ForeignKey
from app.database import Base

class VendorRisk(Base):
    __tablename__ = "vendor_risk"

    id = Column(Integer, primary_key=True, index=True)
    vendor_id = Column(Integer, ForeignKey("vendors.id"))
    total_transactions = Column(Integer)
    fraud_transactions = Column(Integer)
    fraud_ratio = Column(Float)
    risk_score = Column(Float)
    risk_level = Column(String)