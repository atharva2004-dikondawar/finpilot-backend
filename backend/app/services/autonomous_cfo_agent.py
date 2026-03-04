from sqlalchemy.orm import Session

from app.services.ai_cfo_v2 import run_ai_cfo_v2
from app.services.strategy_simulation_engine import run_strategy_simulation
from app.services.ai_cfo_report_engine import generate_cfo_report


def run_autonomous_cfo_agent(db: Session):

    # =====================================
    # 1. Analyze Current Company State
    # =====================================
    intelligence = run_ai_cfo_v2(db)

    health_score = intelligence["health_score"]
    bankruptcy_prob = intelligence["bankruptcy_probability"]

    strategies_tested = []

    # =====================================
    # 2. If Critical → Try Rescue Strategies
    # =====================================
    if health_score < 50 or bankruptcy_prob > 50:

        strategy_options = [
            {"name": "Increase Revenue 20%", "rev": 20, "exp": 0},
            {"name": "Reduce Expenses 20%", "rev": 0, "exp": -20},
            {"name": "Revenue +15% & Expense -15%", "rev": 15, "exp": -15},
        ]

        for s in strategy_options:
            result = run_strategy_simulation(
                db,
                revenue_change=s["rev"],
                expense_change=s["exp"],
                months=12
            )

            strategies_tested.append({
                "strategy": s["name"],
                "estimated_health": result["after_strategy"]["estimated_health_score"],
                "estimated_bankruptcy":
                    result["after_strategy"]["estimated_bankruptcy_probability"],
                "survival_months": result["simulation"]["survival_months"]
            })

        # Select best strategy (lowest bankruptcy probability)
        best_strategy = min(
            strategies_tested,
            key=lambda x: x["estimated_bankruptcy"]
        )

        decision_summary = {
            "action_required": True,
            "recommended_strategy": best_strategy
        }

    else:
        decision_summary = {
            "action_required": False,
            "recommended_strategy": "Maintain current trajectory"
        }

    # =====================================
    # 3. Generate Executive Report
    # =====================================
    report = generate_cfo_report(db)

    # =====================================
    # 4. Final Agent Output
    # =====================================
    return {
        "current_state": intelligence,
        "strategy_analysis": strategies_tested,
        "decision": decision_summary,
        "executive_report": report.get("report", report)
    }