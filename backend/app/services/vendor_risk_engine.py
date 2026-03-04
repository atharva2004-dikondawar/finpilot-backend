from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.company_models import Vendor, Expense
from app.models.fraud_models import FraudScore
from app.models.risk_models import VendorRisk


def calculate_vendor_risk(db: Session):

    # Clear old risk table
    db.query(VendorRisk).delete()

    vendors = db.query(Vendor).all()

    results = []

    for vendor in vendors:

        total_txn = (
            db.query(func.count(Expense.id))
            .filter(Expense.vendor_id == vendor.id)
            .scalar()
        )

        if total_txn == 0:
            continue

        fraud_txn = (
            db.query(func.count(FraudScore.id))
            .join(Expense, FraudScore.transaction_id == Expense.transaction_id)
            .filter(Expense.vendor_id == vendor.id)
            .filter(FraudScore.score >= 60)
            .scalar()
        )

        fraud_ratio = fraud_txn / total_txn if total_txn else 0

        fraud_ratio = fraud_txn / total_txn if total_txn else 0

        # --- TOTAL SPENDING ---
        total_spending = (
            db.query(func.sum(Expense.amount))
            .filter(Expense.vendor_id == vendor.id)
            .scalar()
        ) or 0

        # Normalize spending (simple scaling)
        spending_weight = min(1, total_spending / 500000)   # adjust scale if needed

        # Normalize transaction volume
        volume_weight = min(1, total_txn / 50)

        # Final Weighted Risk Score (0–100)
        risk_score = (
            fraud_ratio * 50
            + spending_weight * 30
            + volume_weight * 20
        )
        risk_score = min(100, risk_score)

        # Risk Level
        if risk_score < 20:
            level = "LOW"
        elif risk_score < 50:
            level = "MEDIUM"
        elif risk_score < 75:
            level = "HIGH"
        else:
            level = "CRITICAL"

        vr = VendorRisk(
            vendor_id=vendor.id,
            total_transactions=total_txn,
            fraud_transactions=fraud_txn,
            fraud_ratio=fraud_ratio,
            risk_score=risk_score,
            risk_level=level
        )

        db.add(vr)

        results.append({
            "vendor": vendor.name,
            "risk_score": risk_score,
            "risk_level": level,
            "fraud_ratio": fraud_ratio
        })

    db.commit()
    return results