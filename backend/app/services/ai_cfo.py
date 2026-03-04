from sqlalchemy.orm import Session
from app.services.ledger_service import get_financial_snapshot
from app.services.forecast_engine import forecast_financials
from app.services.simulation_engine import simulate_future
from app.models.fraud_models import FraudScore
from app.ai.hf_llm import chat_llm

def build_financial_context(db: Session):
    snapshot = get_financial_snapshot(db)

    # ---- MAP SNAPSHOT KEYS SAFELY ----
    cash_balance = snapshot.get("bank_balance") or 0
    monthly_revenue = snapshot.get("total_revenue") or 0
    monthly_expense = snapshot.get("total_expense") or 0
    profit = snapshot.get("profit") or 0

    # ---- FORECAST ----
    try:
        forecast = forecast_financials(db, 6)
        forecast_cash = forecast.get("forecast", {}).get("cash_flow", [])
    except:
        forecast_cash = []

    # ---- SIMULATION ----
    try:
        simulation = simulate_future(db, 0, 0, 6)
        sim_risk = simulation.get("risk_level", "UNKNOWN")
    except:
        sim_risk = "UNKNOWN"

    # ---- FRAUD ----
    fraud_count = db.query(FraudScore).count()

    return {
        "cash_balance": cash_balance,
        "monthly_revenue": monthly_revenue,
        "monthly_expense": monthly_expense,
        "profit": profit,
        "fraud_alerts": fraud_count,
        "forecast_cash": forecast_cash,
        "simulation_risk": sim_risk
    }

def ai_cfo_advice(context):
    advice = []

    if context["cash_balance"] < 0:
        advice.append("Company is running negative cash. Immediate liquidity action required.")

    if context["profit"] < 0:
        advice.append("Company is operating at a loss. Consider reducing expenses or increasing revenue.")

    if context["fraud_alerts"] > 5:
        advice.append("Multiple suspicious transactions detected. Financial audit recommended.")

    if context["simulation_risk"] == "DANGER":
        advice.append("Simulation shows high bankruptcy risk. Cost control and revenue recovery needed.")

    if context["monthly_expense"] > context["monthly_revenue"]:
        advice.append("Expenses exceed revenue. Structural financial imbalance detected.")

    if not advice:
        advice.append("Financial condition is stable. Continue monitoring performance.")

    return advice

def run_ai_cfo(db: Session):
    context = build_financial_context(db)
    advice = ai_cfo_advice(context)

    return {
        "financial_context": context,
        "cfo_advice": advice
    }

def build_cfo_prompt(context, question=None):
    prompt = f"""
You are a highly experienced Chief Financial Officer (CFO).

Analyze the company's financial condition using the data below and provide professional, practical advice.

Financial Data:
- Cash Balance: {context['cash_balance']}
- Monthly Revenue: {context['monthly_revenue']}
- Monthly Expense: {context['monthly_expense']}
- Profit: {context['profit']}
- Fraud Alerts: {context['fraud_alerts']}
- Forecast Cash Trend: {context['forecast_cash']}
- Simulation Risk Level: {context['simulation_risk']}

Explain:
1. Current financial health
2. Major risks
3. Key observations
4. Recommended CFO actions
"""

    if question:
        prompt += f"\nUser Question: {question}\nProvide a clear and concise answer."

    return prompt

def run_llm_cfo(db: Session, question: str = None):
    context = build_financial_context(db)
    prompt = build_cfo_prompt(context, question)

    response = chat_llm.invoke(prompt)

    return {
        "financial_context": context,
        "ai_cfo_analysis": response.content
    }
