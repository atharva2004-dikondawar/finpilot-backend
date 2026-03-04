from app.models.finance_models import FinancialSnapshot
from sqlalchemy.orm import Session


def validate_latest_snapshot(db: Session):

    snapshot = (
        db.query(FinancialSnapshot)
        .order_by(FinancialSnapshot.month.desc())
        .first()
    )

    if not snapshot:
        return {"valid": False, "reason": "No snapshot found"}

    if snapshot.total_revenue <= 0:
        return {"valid": False, "reason": "Revenue is zero or negative"}

    if snapshot.total_expense < 0:
        return {"valid": False, "reason": "Expense invalid"}

    if abs(snapshot.profit) > snapshot.total_revenue * 5:
        return {"valid": False, "reason": "Profit unrealistic"}

    return {"valid": True}