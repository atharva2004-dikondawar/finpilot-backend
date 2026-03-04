from sqlalchemy import Column, Integer, String, Float, ForeignKey, Date
from app.database import Base
from sqlalchemy.orm import relationship

class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)

class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"))
    salary = Column(Float, nullable=False)
    joining_date = Column(Date)
    status = Column(String, default="active")

class Vendor(Base):
    __tablename__ = "vendors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    category = Column(String)   # software, office, infra, contractor, etc.

class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    vendor_id = Column(Integer, ForeignKey("vendors.id"))
    department_id = Column(Integer, ForeignKey("departments.id"))
    transaction_id = Column(Integer, ForeignKey("transactions.id"))  # ADD THIS
    amount = Column(Float)
    description = Column(String)
    date = Column(Date)
