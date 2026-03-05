from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date
import math

from app.models.finance_models import FinancialSnapshot
from app.models.fraud_models import FraudScore
from app.models.department_risk import DepartmentRisk
from app.models.risk_models import VendorRisk
from app.models.company_health import CompanyHealth
from app.services.data_integrity_engine import validate_latest_snapshot
from app.services.revenue_momentum_engine import calculate_revenue_momentum


def calculate_company_health(db: Session):
    
    validation = validate_latest_snapshot(db)
    if not validation["valid"]:
        return {
            "health_score": 10,
            "status": "DATA_ERROR",
            "risk_level": "DANGER",
            "components": {"error": validation["reason"]}
        }
        
    current_month = date.today().replace(day=1)

    snapshot = (
        db.query(FinancialSnapshot)
        .order_by(FinancialSnapshot.month.desc())
        .first()
    )

    if not snapshot:
        return {"error": "No financial snapshot found"}

    # =========================
    # 1. PROFIT SCORE (SMOOTHED)
    # =========================
    profit = snapshot.profit
    revenue = snapshot.total_revenue or 1
    profit_margin = profit / revenue

    # Smooth curve instead of linear explosion
    profit_score = max(0, min(100, (profit_margin + 0.5) * 100))

    # =========================
    # 2. CASH SCORE (LOG SCALE)
    # =========================
    cash = snapshot.cash_balance

    if cash <= 0:
        cash_score = 0
    else:
        cash_score = min(100, math.log10(cash + 1) * 20)

    # =========================
    # 3. FRAUD SCORE (CAPPED)
    # =========================
    total_fraud = db.query(func.count(FraudScore.id)).scalar() or 0
    fraud_penalty = min(60, total_fraud * 1.5)
    fraud_score = max(0, 100 - fraud_penalty)

    # =========================
    # 4. DEPARTMENT SCORE
    # =========================
    avg_dept_risk = db.query(func.avg(DepartmentRisk.risk_score)).scalar() or 0
    dept_score = max(0, 100 - avg_dept_risk)

    # =========================
    # 5. VENDOR SCORE
    # =========================
    avg_vendor_risk = db.query(func.avg(VendorRisk.risk_score)).scalar() or 0
    vendor_score = max(0, 100 - avg_vendor_risk)

        # =========================================
    # STEP D — STRUCTURAL AWARENESS GUARD
    # =========================================

    structural_penalty = 0

    # 1️⃣ Cash Coverage Ratio
    expense = snapshot.total_expense or 1
    cash_ratio = snapshot.cash_balance / expense

    if cash_ratio < -0.5:
        structural_penalty += 20
    elif cash_ratio < 0:
        structural_penalty += 10

    # 2️⃣ Burn Ratio
    burn_ratio = snapshot.profit / expense  # negative if loss

    if burn_ratio < -0.5:
        structural_penalty += 15
    elif burn_ratio < -0.2:
        structural_penalty += 8

    # 3️⃣ Deep Liquidity Crisis
    if snapshot.cash_balance < -1_000_000:
        structural_penalty += 15

    momentum = calculate_revenue_momentum(db)
    momentum_score = momentum["momentum_score"]
    
    # =========================
    # 6. FINAL HEALTH SCORE
    # =========================
    health_score = (
    profit_score * 0.25 +
    cash_score * 0.20 +
    fraud_score * 0.10 +
    dept_score * 0.10 +
    vendor_score * 0.10 +
    momentum_score * 0.25
    ) - structural_penalty

    # Stability clamp (no instant 0 or 100)
    health_score = float(max(10, min(95, health_score)))

    # =========================
    # STATUS
    # =========================
    if health_score >= 75:
        status = "STRONG"
        risk_level = "LOW"
    elif health_score >= 55:
        status = "STABLE"
        risk_level = "MODERATE"
    elif health_score >= 35:
        status = "WEAK"
        risk_level = "HIGH"
    else:
        status = "CRITICAL"
        risk_level = "DANGER"

    # =========================
    # UPSERT
    # =========================
    existing = (
        db.query(CompanyHealth)
        .filter(CompanyHealth.month == current_month)
        .first()
    )

    if existing:
        existing.health_score = float(health_score)
        existing.status = status
        existing.risk_level = risk_level
    else:
        db.add(CompanyHealth(
            month=current_month,
            health_score=float(health_score),
            status=status,
            risk_level=risk_level
        ))

    db.commit()

    return {
        "health_score": round(health_score, 2),
        "status": status,
        "risk_level": risk_level,
        "components": {
            "profit_score": profit_score,
            "cash_score": cash_score,
            "fraud_score": fraud_score,
            "department_score": dept_score,
            "vendor_score": vendor_score
        }
    }