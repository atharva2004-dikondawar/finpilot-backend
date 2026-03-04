from sqlalchemy.orm import Session
from huggingface_hub import InferenceClient
import os

from app.services.ai_cfo_v2 import run_ai_cfo_v2


client = InferenceClient(
    api_key=os.getenv("HUGGINGFACEHUB_API_TOKEN")
)


def generate_cfo_report(db: Session):

    data = run_ai_cfo_v2(db)

    prompt = f"""
You are an expert Chief Financial Officer.

Generate a professional executive financial report.

Company State: {data['company_state']}
Health Score: {data['health_score']}
Bankruptcy Probability: {data['bankruptcy_probability']}%
Survival Months: {data['survival_months']}

Top Risks: {data['top_risks']}
Recommended Actions: {data['recommended_actions']}
Financial Analysis: {data['financial_analysis']}
Insight Summary: {data['insight_summary']}

Write:
1. Executive Summary
2. Financial Risk Analysis
3. Strategic Recommendations
4. Financial Outlook
"""

    try:
        completion = client.chat.completions.create(
            model="mistralai/Mistral-7B-Instruct-v0.2",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=700,
            temperature=0.4
        )

        report_text = completion.choices[0].message.content

        return {
            "company_state": data["company_state"],
            "health_score": data["health_score"],
            "bankruptcy_probability": data["bankruptcy_probability"],
            "report": report_text
        }

    except Exception as e:
        return {"error": str(e)}