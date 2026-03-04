from sqlalchemy.orm import Session
from app.services.simulation_engine import simulate_future
from app.services.company_health_engine import calculate_company_health
from app.services.bankruptcy_engine import calculate_bankruptcy_risk


def run_strategy_simulation(
    db: Session,
    revenue_change: float = 0,
    expense_change: float = 0,
    months: int = 12,
    funding_injection: float = 0,   # NEW
    fixed_cost_cut: float = 0       # NEW
):

    # -------------------------------
    # 1. Baseline (Current State)
    # -------------------------------
    base_health = calculate_company_health(db)
    base_bankruptcy = calculate_bankruptcy_risk(db)

    # -------------------------------
    # 2. Run Simulation
    # -------------------------------
    sim = simulate_future(
        db,
        revenue_change=revenue_change,
        expense_change=expense_change,
        months=months,
        funding_injection=funding_injection,
        fixed_cost_cut=fixed_cost_cut
    )

    survival = sim["cash_runway_months"] or 1

    # -------------------------------
    # 3. Estimate Health After Strategy
    # -------------------------------
    # Simple estimation logic (can be improved later)
    est_health = max(0, min(100,
        base_health["health_score"]
        + (revenue_change * 0.8)
        - (expense_change * 0.5)
        + (funding_injection / 1000000)
    ))

    # -------------------------------
    # 4. Estimate Bankruptcy
    # -------------------------------
    est_bankruptcy = max(1, min(95,
        base_bankruptcy["bankruptcy_probability"]
        - (revenue_change * 0.5)
        - (survival * 2)
        - (funding_injection / 2000000)
    ))

    return {
        "inputs": {
            "revenue_change_pct": revenue_change,
            "expense_change_pct": expense_change,
            "months": months,
            "funding_injection": funding_injection,
            "fixed_cost_cut": fixed_cost_cut
        },
        "baseline": {
            "health_score": base_health["health_score"],
            "bankruptcy_probability": base_bankruptcy["bankruptcy_probability"]
        },
        "simulation": {
            "final_cash": sim["simulated_cash"][-1],
            "survival_months": survival,
            "simulated_cash_curve": sim["simulated_cash"]
        },
        "after_strategy": {
            "estimated_health_score": round(est_health, 2),
            "estimated_bankruptcy_probability": round(est_bankruptcy, 2)
        }
    }