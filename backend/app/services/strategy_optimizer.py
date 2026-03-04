from sqlalchemy.orm import Session
import itertools
from app.services.strategy_simulation_engine import run_strategy_simulation

def run_strategy_optimizer(db: Session):

    revenue_options = [-20, -10, 0, 10, 20, 30, 40]
    expense_options = [-40, -30, -20, -10, 0, 10, 20]

    results = []

    for rev, exp in itertools.product(revenue_options, expense_options):

        try:
            sim = run_strategy_simulation(
                db,
                revenue_change=rev,
                expense_change=exp,
                months=12
            )

            health = sim["after_strategy"]["estimated_health_score"]
            bankruptcy = sim["after_strategy"]["estimated_bankruptcy_probability"]
            survival = sim["simulation"]["survival_months"]

            # Normalize survival to 0-100 scale (max 36 months)
            survival_score = min(100, (survival / 36) * 100)

            # Revenue growth bonus — reward strategies that grow revenue
            revenue_bonus = max(0, rev) * 0.05

            # Expense efficiency bonus — reward cutting expenses more than revenue growth
            efficiency_bonus = max(0, -exp) * 0.03

            final_score = (
                health * 0.30 +
                (100 - bankruptcy) * 0.30 +
                survival_score * 0.25 +
                revenue_bonus +
                efficiency_bonus
            )

            results.append({
                "revenue_change": rev,
                "expense_change": exp,
                "health_score": health,
                "bankruptcy_probability": bankruptcy,
                "survival_months": survival,
                "final_score": round(final_score, 2)
            })

        except Exception as e:
            print(f"Strategy failed: rev={rev}, exp={exp} → {e}")

    if not results:
        return {"error": "No valid strategies evaluated."}

    results_sorted = sorted(results, key=lambda x: -x["final_score"])

    best_strategy = results_sorted[0]
    top_5 = results_sorted[:5]

    avg_score = sum(r["final_score"] for r in results) / len(results)
    best_score = results_sorted[0]["final_score"]
    worst_score = results_sorted[-1]["final_score"]
    score_range = best_score - worst_score

    # Confidence = how far best is above average, normalized to 100
    confidence = max(0, min(100,
        ((best_score - avg_score) / (score_range + 0.001)) * 100
    ))


    return {
        "best_strategy": best_strategy,
        "top_strategies": top_5,
        "confidence_score": round(confidence, 2),
        "strategies_tested": len(results)
    }