from sqlalchemy.orm import Session

# Core Engines
from app.services.company_health_engine import calculate_company_health
from app.services.forecast_engine import forecast_financials
from app.services.simulation_engine import simulate_future
from app.services.fraud_engine import get_fraud_trend
from app.services.vendor_risk_engine import calculate_vendor_risk
from app.services.department_risk_engine import calculate_department_risk
from app.services.bankruptcy_engine import calculate_bankruptcy_risk
from app.services.financial_reason_engine import generate_financial_reasoning


def run_ai_cfo_v2(db: Session):

    # =========================================================
    # 1. COLLECT INTELLIGENCE
    # =========================================================
    health = calculate_company_health(db)
    forecast = forecast_financials(db, months=6)
    fraud = get_fraud_trend(db)
    vendors = calculate_vendor_risk(db)
    departments = calculate_department_risk(db)
    simulation = simulate_future(db, revenue_change=0, expense_change=0, months=6)
    bankruptcy = calculate_bankruptcy_risk(db)
    reasoning = generate_financial_reasoning(db)

    # =========================================================
    # 2. EXTRACT KEY SIGNALS
    # =========================================================
    health_score = health["health_score"]
    cash_runway = simulation["cash_runway_months"] or 12
    fraud_rate = fraud.get("fraud_rate", 0)
    bankruptcy_prob = bankruptcy["bankruptcy_probability"]

    risks = []
    actions = []
    insight = []
    priority = "NORMAL"

    # =========================================================
    # 3. FINANCIAL HEALTH RISK
    # =========================================================
    if health_score < 35:
        risks.append("Company financial health critical")
        actions.append("Immediate financial restructuring required")
        priority = "EMERGENCY"

    # =========================================================
    # 4. CASH RUNWAY RISK
    # =========================================================
    if cash_runway <= 3:
        risks.append("Low cash runway")
        actions.append("Secure funding or reduce burn rate immediately")
        priority = "EMERGENCY"

    # =========================================================
    # 5. BANKRUPTCY RISK
    # =========================================================
    if bankruptcy_prob > 70:
        risks.append("High bankruptcy probability")
        actions.append("Activate survival strategy and liquidity protection")
        priority = "EMERGENCY"

    # =========================================================
    # 6. PROFITABILITY RISK
    # =========================================================
    if health["components"]["profit_score"] < 30:
        risks.append("Loss making operations")
        actions.append("Reduce operational cost and improve margins")

    # =========================================================
    # 7. FRAUD RISK
    # =========================================================
    if fraud_rate > 0.08:
        risks.append("Fraud exposure present")
        actions.append("Strengthen audit and monitoring systems")

    # =========================================================
    # 8. DEPARTMENT RISK
    # =========================================================
    high_dept = [d for d in departments if d["risk_level"] in ["HIGH", "CRITICAL"]]
    if high_dept:
        risks.append("High risk departments detected")
        actions.append("Audit and control high risk department spending")

    # =========================================================
    # 9. VENDOR RISK
    # =========================================================
    high_vendor = [v for v in vendors if v["risk_level"] in ["HIGH", "CRITICAL"]]
    if high_vendor:
        risks.append("Risky vendors detected")
        actions.append("Review vendor contracts and payment patterns")

    # =========================================================
    # 10. GROWTH STRATEGY (ONLY IF STABLE)
    # =========================================================
    if health_score > 55 and bankruptcy_prob < 40:
        actions.append("Invest in controlled growth and expansion")

    # =========================================================
    # 11. EXPLAINABLE FINANCIAL INSIGHT
    # =========================================================
    if reasoning and "error" not in reasoning:

        insight.append(
            f"Revenue trend {reasoning['revenue_trend_pct']}% | "
            f"Expense trend {reasoning['expense_trend_pct']}%"
        )

        insight.append(
            f"Burn rate ≈ {reasoning['burn_rate_per_month']} per month | "
            f"Cash balance {reasoning['cash_balance']}"
        )

        insight.append(
            f"Estimated cash runway ≈ {reasoning['cash_runway_estimate_months']} months"
        )

    # =========================================================
    # 12. DETERMINE COMPANY STATE
    # =========================================================
    if health_score < 30:
        state = "CRITICAL"
    elif health_score < 50:
        state = "WEAK"
    elif health_score < 70:
        state = "STABLE"
    else:
        state = "HEALTHY"

    # =========================================================
    # 13. FINAL OUTPUT
    # =========================================================
    return {
        "company_state": state,
        "health_score": round(health_score, 2),
        "bankruptcy_probability": round(bankruptcy_prob, 2),
        "survival_months": cash_runway,
        "top_risks": risks,
        "recommended_actions": actions,
        "financial_analysis": reasoning,
        "insight_summary": insight,
        "priority": priority
    }