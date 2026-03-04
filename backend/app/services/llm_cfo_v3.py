from sqlalchemy.orm import Session
from app.services.company_health_engine import calculate_company_health
from app.services.simulation_engine import simulate_future
from app.services.forecast_engine import forecast_financials

from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace


# --- Load LLM ---
llm = HuggingFaceEndpoint(
    repo_id="mistralai/Mistral-7B-Instruct-v0.3",
    task="text-generation",
    temperature=0.4,
    max_new_tokens=512
)

chat_llm = ChatHuggingFace(llm=llm)

def run_llm_cfo_v3(db: Session):

    health = calculate_company_health(db)
    sim = simulate_future(db, 0, 0, 6)
    forecast = forecast_financials(db, 6)

    prompt = f"""
You are a professional Chief Financial Officer (CFO).

Analyze the company's financial condition using DATA and provide a fact-based strategic report.

===== FINANCIAL DATA =====

Health Score: {health['health_score']}
Company Status: {health['status']}
Risk Level: {health['risk_level']}

Cash Runway (months): {sim['cash_runway_months']}
Simulation Risk: {sim['risk_level']}

Forecast Revenue: {forecast['forecast']['revenue']}
Forecast Expense: {forecast['forecast']['expense']}

===== INSTRUCTIONS =====

Your report MUST include:

1. Financial Diagnosis (with numbers)
2. Key Financial Problems (with causes)
3. Risk Analysis (cash, fraud, operations)
4. Trend Analysis (revenue vs expense direction)
5. Strategic CFO Actions (data-backed)
6. Stability Outlook (short + long term)
7. Confidence Level (Low / Medium / High)

Be analytical, concise, and professional. Think like a real CFO.
Explain WHY each conclusion is reached using numbers.
"""

    response = chat_llm.invoke(prompt)

    return {
    "financial_state": health,
    "simulation": sim,
    "forecast_summary": {
        "avg_revenue": sum(forecast['forecast']['revenue']) / len(forecast['forecast']['revenue']),
        "avg_expense": sum(forecast['forecast']['expense']) / len(forecast['forecast']['expense'])
    },
    "llm_cfo_report": response.content
}