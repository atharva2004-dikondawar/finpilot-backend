from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.company_models import Department, Expense
from app.models.fraud_models import FraudScore
from app.models.department_risk import DepartmentRisk


def calculate_department_risk(db: Session):

    # Clear previous results (recompute fresh)
    db.query(DepartmentRisk).delete()

    departments = db.query(Department).all()

    results = []

    for dept in departments:

        # --- Total Expense ---
        total_expense = (
            db.query(func.sum(Expense.amount))
            .filter(Expense.department_id == dept.id)
            .scalar()
        ) or 0

        # --- Total Transactions ---
        total_txn = (
            db.query(func.count(Expense.id))
            .filter(Expense.department_id == dept.id)
            .scalar()
        )

        if total_txn == 0:
            continue

        # --- Fraud Transactions ---
        fraud_txn = (
            db.query(func.count(FraudScore.id))
            .join(Expense, FraudScore.transaction_id == Expense.transaction_id)
            .filter(Expense.department_id == dept.id)
            .filter(FraudScore.score >= 60)   # High-risk threshold
            .scalar()
        )

        fraud_ratio = fraud_txn / total_txn if total_txn else 0

        # --- Risk Calculation ---
        expense_weight = min(1, total_expense / 600000)
        fraud_weight = min(1, fraud_ratio)

        risk_score = (
            fraud_weight * 60 +
            expense_weight * 40
        )

        risk_score = min(100, risk_score)

        # --- Risk Level ---
        if risk_score < 20:
            level = "LOW"
        elif risk_score < 50:
            level = "MEDIUM"
        elif risk_score < 75:
            level = "HIGH"
        else:
            level = "CRITICAL"

        # Store in DB
        dr = DepartmentRisk(
            department_id=dept.id,
            total_expense=total_expense,
            fraud_transactions=fraud_txn,
            fraud_ratio=fraud_ratio,
            risk_score=risk_score,
            risk_level=level
        )

        db.add(dr)

        results.append({
            "department": dept.name,
            "total_expense": total_expense,
            "fraud_ratio": fraud_ratio,
            "risk_score": risk_score,
            "risk_level": level
        })

    db.commit()

    return results