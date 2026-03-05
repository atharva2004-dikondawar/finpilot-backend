from sqlalchemy.orm import Session
from groq import Groq
import os

from app.services.ai_cfo_v2 import run_ai_cfo_v2

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def generate_cfo_report(db: Session):
    data = run_ai_cfo_v2(db)

    prompt = f"""You are an expert Chief Financial Officer.

Generate a professional executive financial report.

Company State: {data['company_state']}
Health Score: {data['health_score']}
Bankruptcy Probability: {data['bankruptcy_probability']}%
Survival Months: {data['survival_months']}

Top Risks: {data['top_risks']}
Recommended Actions: {data['recommended_actions']}
Financial Analysis: {data['financial_analysis']}
Insight Summary: {data['insight_summary']}

Write exactly in this format:
1. Executive Summary:
[content]

2. Financial Risk Analysis:
[content]

3. Strategic Recommendations:
[content]

4. Financial Outlook:
[content]
"""

    try:
        completion = client.chat.completions.create(
            model="llama3-8b-8192",
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