from sqlalchemy.orm import Session
import numpy as np
from app.models.finance_models import FinancialSnapshot


def calculate_revenue_momentum(db: Session):

    snapshots = (
        db.query(FinancialSnapshot)
        .order_by(FinancialSnapshot.month.asc())
        .all()
    )

    if len(snapshots) < 4:
        return {
            "momentum_score": 50,
            "trend": "INSUFFICIENT_DATA",
            "growth_rate": 0,
            "acceleration": 0,
            "volatility": 0
        }

    revenue = np.array([s.total_revenue for s in snapshots])
    
    growth_rates = np.diff(revenue) / np.maximum(revenue[:-1], 1)

    avg_growth = np.mean(growth_rates) * 100
    
    if len(growth_rates) >= 2:
        acceleration = np.mean(np.diff(growth_rates)) * 100
    else:
        acceleration = 0
    
    volatility = np.std(growth_rates) * 100
    
    if avg_growth > 5:
        trend = "STRONG_GROWTH"
    elif avg_growth > 1:
        trend = "STABLE_GROWTH"
    elif avg_growth > -2:
        trend = "FLAT"
    elif avg_growth > -6:
        trend = "DECLINE"
    else:
        trend = "SEVERE_DECLINE"
        
    score = 50

    # Growth contribution
    score += avg_growth * 2

    # Acceleration contribution
    score += acceleration * 1.5

    # Volatility penalty
    score -= volatility * 1.2

    score = max(0, min(100, score))
    
    return {
        "momentum_score": round(score, 2),
        "trend": trend,
        "growth_rate": round(avg_growth, 2),
        "acceleration": round(acceleration, 2),
        "volatility": round(volatility, 2)
    }