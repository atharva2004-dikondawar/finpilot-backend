from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.finance_models import FinancialSnapshot


def generate_financial_reasoning(db: Session):

    snapshots = (
        db.query(FinancialSnapshot)
        .order_by(FinancialSnapshot.month.asc())
        .all()
    )

    if len(snapshots) < 2:
        return {"error": "Not enough history"}

    latest = snapshots[-1]
    prev = snapshots[-2]

    # --- Revenue Trend % ---
    revenue_trend = 0
    if prev.total_revenue:
        revenue_trend = ((latest.total_revenue - prev.total_revenue) / prev.total_revenue) * 100

    # --- Expense Trend % ---
    expense_trend = 0
    if prev.total_expense:
        expense_trend = ((latest.total_expense - prev.total_expense) / prev.total_expense) * 100

    # --- Burn Rate ---
    burn_rate = latest.total_expense - latest.total_revenue

    # --- Cash Runway ---
    if burn_rate > 0:
        runway = latest.cash_balance / burn_rate
    else:
        runway = 12  # safe assumption

    return {
        "revenue_trend_pct": round(revenue_trend, 2),
        "expense_trend_pct": round(expense_trend, 2),
        "burn_rate_per_month": round(burn_rate, 2),
        "cash_balance": round(latest.cash_balance, 2),
        "cash_runway_estimate_months": round(runway, 2)
    }