from sqlalchemy.orm import Session
from datetime import date
from sqlalchemy import func

from app.models.finance_models import FinancialSnapshot
from app.models.company_health import CompanyHealth
from app.models.fraud_models import FraudScore
from app.models.risk_models import VendorRisk
from app.models.department_risk import DepartmentRisk
from app.models.bankruptcy_model import BankruptcyRisk

from app.services.simulation_engine import simulate_future
from app.services.revenue_momentum_engine import calculate_revenue_momentum

def calculate_bankruptcy_risk(db: Session):

    current_month = date.today().replace(day=1)

    snapshot = (
        db.query(FinancialSnapshot)
        .order_by(FinancialSnapshot.month.desc())
        .first()
    )

    if not snapshot:
        return {"error": "No financial snapshot found"}

    revenue = snapshot.total_revenue or 1
    profit = snapshot.profit
    profit_margin = profit / revenue

    health = (
        db.query(CompanyHealth)
        .order_by(CompanyHealth.month.desc())
        .first()
    )
    health_score = health.health_score if health else 50

    # =========================
    # FRAUD / VENDOR / DEPT
    # =========================
    fraud_count = db.query(func.count(FraudScore.id)).scalar() or 0
    fraud_factor = min(1, fraud_count / 120)

    avg_vendor_risk = db.query(func.avg(VendorRisk.risk_score)).scalar() or 0
    vendor_factor = avg_vendor_risk / 100

    avg_dept_risk = db.query(func.avg(DepartmentRisk.risk_score)).scalar() or 0
    dept_factor = avg_dept_risk / 100

    # =========================
    # RUNWAY (SMOOTHED)
    # =========================
    sim = simulate_future(db, 0, 0, 12)
    runway = sim["cash_runway_months"] or 12
    runway_factor = max(0, 1 - (runway / 18))

    # =========================
    # STRUCTURAL BASE RISK
    # =========================
    # Higher baseline for companies with limited history
    snapshot_count = db.query(FinancialSnapshot).count()
    if snapshot_count < 3:
        structural_risk = 0.15  # new company premium
    elif snapshot_count < 12:
        structural_risk = 0.10  # early stage
    else:
        structural_risk = 0.08  # established
    
    # =========================
    # MOMENTUM FACTOR
    # =========================
    momentum = calculate_revenue_momentum(db)
    momentum_factor = (100 - momentum["momentum_score"]) / 100
    
    # =========================
    # CORE MODEL
    # =========================
    risk_score = (
        (1 - max(0, profit_margin)) * 0.20 +
        (1 - health_score / 100) * 0.25 +
        fraud_factor * 0.10 +
        vendor_factor * 0.10 +
        dept_factor * 0.10 +
        runway_factor * 0.17 +
        structural_risk
    )
    risk_score += momentum_factor * 0.12
    
    probability = max(0.05, min(0.92, risk_score))

    # =========================
    # RISK LEVEL
    # =========================
    if probability < 0.25:
        level = "LOW"
    elif probability < 0.5:
        level = "MEDIUM"
    elif probability < 0.75:
        level = "HIGH"
    else:
        level = "EXTREME"

    # =========================
    # UPSERT
    # =========================
    existing = (
        db.query(BankruptcyRisk)
        .filter(BankruptcyRisk.month == current_month)
        .first()
    )

    if existing:
        existing.probability = float(probability)
        existing.risk_level = level
        existing.survival_months = int(runway)
    else:
        db.add(BankruptcyRisk(
            month=current_month,
            probability=float(probability),
            risk_level=level,
            survival_months=int(runway)
        ))

    db.commit()

    return {
        "bankruptcy_probability": round(float(probability) * 100, 2),
        "risk_level": level,
        "survival_months": int(runway)
    }