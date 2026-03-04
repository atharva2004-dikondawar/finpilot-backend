import numpy as np
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from collections import defaultdict

from app.models.finance_models import Transaction


def build_monthly_series(db: Session):
    transactions = db.query(Transaction).all()

    monthly_revenue = defaultdict(float)
    monthly_expense = defaultdict(float)
    monthly_cash = defaultdict(float)

    for txn in transactions:
        month_key = txn.created_at.strftime("%Y-%m")

        # Revenue: credit to revenue account (3)
        if txn.credit_account_id == 3:
            monthly_revenue[month_key] += txn.amount

        # Expense: debit to expense accounts (2,4)
        if txn.debit_account_id in [2, 4]:
            monthly_expense[month_key] += txn.amount

        # Cash flow: debit bank = inflow, credit bank = outflow
        if txn.debit_account_id == 1:
            monthly_cash[month_key] += txn.amount
        elif txn.credit_account_id == 1:
            monthly_cash[month_key] -= txn.amount

    # Sort months
    months = sorted(monthly_cash.keys())

    revenue_series = [monthly_revenue[m] for m in months]
    expense_series = [monthly_expense[m] for m in months]
    cash_series = [monthly_cash[m] for m in months]

    return months, revenue_series, expense_series, cash_series

def linear_forecast(series, steps=6, growth_rate=0.03):
    if len(series) < 2:
        # Apply modest 3% monthly growth assumption when insufficient history
        base = series[-1] if series else 0
        return [round(base * ((1 + growth_rate) ** i), 2) for i in range(1, steps + 1)]

    x = np.arange(len(series))
    y = np.array(series)

    # Fit line y = ax + b
    a, b = np.polyfit(x, y, 1)

    future = []
    for i in range(1, steps + 1):
        future.append(float(a * (len(series) + i) + b))

    return future

def forecast_financials(db: Session, months: int = 6):

    # Build historical series
    months_history, revenue_series, expense_series, cash_series = build_monthly_series(db)

    if not months_history:
        return {"error": "Not enough historical data for forecasting"}

    # Forecast using linear regression
    revenue_forecast = linear_forecast(revenue_series, months)
    expense_forecast = linear_forecast(expense_series, months)
    cash_forecast = linear_forecast(cash_series, months)

    # Generate future month labels
    future_months = []
    last_month = datetime.strptime(months_history[-1], "%Y-%m")

    for i in range(1, months + 1):
        future_date = last_month + timedelta(days=30*i + i*2)
        future_months.append(future_date.strftime("%Y-%m"))

    return {
        "history": {
            "months": months_history,
            "revenue": revenue_series,
            "expense": expense_series,
            "cash_flow": cash_series
        },
        "forecast": {
            "months": future_months,
            "revenue": revenue_forecast,
            "expense": expense_forecast,
            "cash_flow": cash_forecast
        }
    }