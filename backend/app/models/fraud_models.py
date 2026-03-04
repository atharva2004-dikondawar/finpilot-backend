from sqlalchemy import Column, Integer, Float, ForeignKey, String
from app.database import Base

class FraudScore(Base):
    __tablename__ = "fraud_scores"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id"))
    score = Column(Float)
    explanation = Column(String)

