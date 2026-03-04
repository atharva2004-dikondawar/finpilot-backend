import numpy as np
from sqlalchemy.orm import Session
from app.services.forecast_engine import forecast_financials


def simulate_future(
    db: Session,
    revenue_change: float = 0,
    expense_change: float = 0,
    months: int = 6,
    funding_injection: float = 0,
    fixed_cost_cut: float = 0
):

    data = forecast_financials(db, months)

    # -----------------------------
    # Starting Cash
    # -----------------------------
    cash = data["history"]["cash_flow"][-1] + funding_injection

    revenue_forecast = data["forecast"]["revenue"]
    expense_forecast = data["forecast"]["expense"]

    simulated_cash = []
    runway = None
    break_even_month = None

    # -----------------------------
    # REALISM PARAMETERS
    # -----------------------------
    growth_decay = 0.88              # growth fades
    expense_stickiness = 0.65        # cost cuts partially effective
    operating_leverage = 0.08        # revenue growth increases some costs
    friction_factor = 0.15           # extreme strategy penalty

    for i in range(months):

        # -----------------------------
        # Revenue Adjustment (Decaying)
        # -----------------------------
        effective_revenue_change = (
            revenue_change *
            (growth_decay ** i)
        )

        rev = revenue_forecast[i] * (1 + effective_revenue_change / 100)

        # -----------------------------
        # Expense Adjustment (Sticky)
        # -----------------------------
        effective_expense_change = expense_change * expense_stickiness

        exp = expense_forecast[i] * (1 + effective_expense_change / 100)

        # Apply structural fixed cost cut gradually
        exp = max(0, exp - (fixed_cost_cut * (i + 1) / months))

        # -----------------------------
        # Operating Leverage Effect
        # -----------------------------
        exp += rev * operating_leverage

        # -----------------------------
        # Strategy Friction (extreme penalty)
        # -----------------------------
        extremity = abs(revenue_change) + abs(expense_change)

        if extremity > 40:
            friction_penalty = extremity * friction_factor
            rev *= (1 - friction_penalty / 200)

        # -----------------------------
        # Net Cash Flow
        # -----------------------------
        net = rev - exp
        cash += net

        # Hard floor protection
        if cash < -5e9:
            cash = -5e9

        simulated_cash.append(round(cash, 2))

        # Detect break-even
        if net >= 0 and break_even_month is None:
            break_even_month = i + 1

        # Detect runway
        if cash <= 0 and runway is None:
            runway = i + 1

    # -----------------------------
    # Final Runway Handling
    # -----------------------------
    if runway is None:
        last_cash = simulated_cash[-1]
        monthly_changes = [
            simulated_cash[i] - (simulated_cash[i-1] if i > 0 else 0)
            for i in range(len(simulated_cash))
        ]
        negative_changes = [c for c in monthly_changes if c < 0]
        avg_monthly_burn = abs(sum(negative_changes) / len(negative_changes)) if negative_changes else 0

        if avg_monthly_burn > 0:
            runway = min(120, months + int(last_cash / avg_monthly_burn))
        else:
            runway = 120  # Profitable indefinitely

    # Risk based on cash trend, not just runway
    final_cash = simulated_cash[-1]
    initial_cash = simulated_cash[0] if simulated_cash else 0
    starting_cash = data["history"]["cash_flow"][-1]

    # Calculate cash change percentage
    if starting_cash > 0:
        cash_change_pct = (final_cash - starting_cash) / starting_cash * 100
    elif starting_cash < 0:
        cash_change_pct = -100
    else:
        cash_change_pct = 0

    # Monthly net flows — are we burning or growing?
    monthly_nets = []
    for i in range(len(simulated_cash)):
        prev = starting_cash if i == 0 else simulated_cash[i-1]
        monthly_nets.append(simulated_cash[i] - prev)

    avg_monthly_net = sum(monthly_nets) / len(monthly_nets)
    negative_months = sum(1 for n in monthly_nets if n < 0)

    # Determine risk
    if runway < months * 0.5:
        risk = "DANGER"
    elif runway < months * 0.75 or negative_months > months * 0.5:
        risk = "WARNING"
    elif cash_change_pct < -20 or avg_monthly_net < 0:
        risk = "WARNING"
    else:
        risk = "SAFE"

    return {
        "simulated_cash": simulated_cash,
        "cash_runway_months": runway,
        "break_even_month": break_even_month,
        "risk_level": risk,
        "cash_change_pct": round(cash_change_pct, 1),
        "avg_monthly_net": round(avg_monthly_net, 2),
    }