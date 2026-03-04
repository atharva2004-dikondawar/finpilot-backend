from statistics import stdev
from app.services.strategy_simulation_engine import run_strategy_simulation


def analyze_strategy_stability(db, revenue_change, expense_change, months=12):

    result = run_strategy_simulation(
        db,
        revenue_change=revenue_change,
        expense_change=expense_change,
        months=months
    )

    cash_curve = result["simulation"]["simulated_cash_curve"]
    survival = result["simulation"]["survival_months"]
    bankruptcy = result["after_strategy"]["estimated_bankruptcy_probability"]
    health = result["after_strategy"]["estimated_health_score"]

    # =============================
    # 1. Cash Volatility
    # =============================
    if len(cash_curve) > 2:
        volatility = stdev(cash_curve)
    else:
        volatility = 0

    volatility_score = max(0, 100 - (volatility / 100000))

    # =============================
    # 2. Survival Stability
    # =============================
    survival_score = min(100, survival * 8)

    # =============================
    # 3. Bankruptcy Sensitivity
    # =============================
    bankruptcy_score = max(0, 100 - bankruptcy)

    # =============================
    # 4. Health Consistency
    # =============================
    health_score = health

    # =============================
    # FINAL STABILITY SCORE
    # =============================
    stability_score = (
        volatility_score * 0.30 +
        survival_score * 0.25 +
        bankruptcy_score * 0.25 +
        health_score * 0.20
    )

    # =============================
    # STABILITY LEVEL
    # =============================
    if stability_score >= 75:
        level = "STABLE"
    elif stability_score >= 55:
        level = "MODERATE"
    elif stability_score >= 35:
        level = "UNSTABLE"
    else:
        level = "DANGEROUS"

    return {
        "stability_score": round(stability_score, 2),
        "stability_level": level,
        "volatility_score": round(volatility_score, 2),
        "survival_score": round(survival_score, 2),
        "bankruptcy_score": round(bankruptcy_score, 2),
        "health_score": round(health_score, 2)
    }