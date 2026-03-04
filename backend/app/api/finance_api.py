from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import SessionLocal

from app.services.ledger_service import create_transaction, get_account_balance, calculate_profit_loss, process_monthly_payroll, record_expense, get_financial_snapshot, generate_monthly_snapshot
from app.services.data_generator import generate_company_history
from app.services.fraud_engine import run_fraud_detection, get_fraud_trend
from app.services.forecast_engine import forecast_financials
from app.services.simulation_engine import simulate_future
from app.services.ai_cfo import run_ai_cfo, run_llm_cfo
from app.services.vendor_risk_engine import calculate_vendor_risk
from app.services.department_risk_engine import calculate_department_risk
from app.services.company_health_engine import calculate_company_health
from app.services.ai_cfo_v2 import run_ai_cfo_v2
from app.services.bankruptcy_engine import calculate_bankruptcy_risk
from app.services.strategy_simulation_engine import run_strategy_simulation
from app.services.ai_cfo_report_engine import generate_cfo_report
from app.services.autonomous_cfo_agent import run_autonomous_cfo_agent
from app.services.strategy_optimizer import run_strategy_optimizer
from app.services.revenue_momentum_engine import calculate_revenue_momentum

from app.models.finance_models import Account, Transaction
from app.models.fraud_models import FraudScore
from app.models.risk_models import VendorRisk
from app.models.company_models import Vendor

from datetime import date

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/transaction")
def add_transaction(
    description: str,
    amount: float,
    debit_account_id: int,
    credit_account_id: int,
    db: Session = Depends(get_db)
):
    txn = create_transaction(
        db,
        description,
        amount,
        debit_account_id,
        credit_account_id
    )
    return {"transaction_id": txn.id}

@router.post("/seed-accounts")
def seed_accounts(db: Session = Depends(get_db)):
    from app.models.finance_models import Account
    existing = db.query(Account).count()
    if existing > 0:
        return {"message": f"Accounts already exist ({existing} found)"}
    
    accounts = [
        Account(id=1, name="Bank",           type="asset",   account_type="ASSET"),
        Account(id=2, name="Salary Expense", type="expense",  account_type="EXPENSE"),
        Account(id=3, name="Revenue",        type="revenue",  account_type="REVENUE"),
        Account(id=4, name="Vendor Expense", type="expense",  account_type="EXPENSE"),
        Account(id=6, name="Owner Equity",   type="equity",   account_type="EQUITY"),
    ]
    db.add_all(accounts)
    db.commit()
    return {"message": "✅ Accounts seeded successfully"}

@router.get("/balance/{account_id}")
def get_balance(account_id: int, db: Session = Depends(get_db)):
    balance = get_account_balance(db, account_id)
    return {"account_id": account_id, "balance": balance}

@router.get("/profit-loss")
def get_profit_loss(db: Session = Depends(get_db)):
    return calculate_profit_loss(db)

@router.post("/process-payroll")
def run_payroll(db: Session = Depends(get_db)):
    return process_monthly_payroll(db)
@router.post("/record-expense")
def add_expense(
    vendor_id: int,
    department_id: int,
    amount: float,
    description: str,
    db: Session = Depends(get_db)
):
    return record_expense(
        db,
        vendor_id,
        department_id,
        amount,
        description,
        date.today()
    )

@router.get("/financial-snapshot")
def financial_snapshot(db: Session = Depends(get_db)):
    return get_financial_snapshot(db)

@router.post("/generate-history")
def generate_history(months: int = 24, db: Session = Depends(get_db)):
    return generate_company_history(db, months, base_revenue=150000)

@router.post("/run-fraud-detection")
def fraud_detection(db: Session = Depends(get_db)):
    return run_fraud_detection(db)

@router.get("/suspicious-transactions")
def get_suspicious(db: Session = Depends(get_db)):
    results = (
        db.query(FraudScore, Transaction)
        .join(Transaction, FraudScore.transaction_id == Transaction.id)
        .filter(FraudScore.score >= 60)
        .all()
    )

    output = []
    for fs, txn in results:
        output.append({
            "transaction_id": txn.id,
            "description": txn.description,
            "amount": txn.amount,
            "fraud_score": fs.score,
            "reason": fs.explanation,
            "debit_account": txn.debit_account_id,
            "credit_account": txn.credit_account_id
        })

    return output

@router.get("/forecast")
def get_forecast(months: int = 6, db: Session = Depends(get_db)):
    return forecast_financials(db, months)

@router.get("/simulate")
def run_simulation(
    revenue_change: float = 0,
    expense_change: float = 0,
    months: int = 12,
    db: Session = Depends(get_db)
):
    return simulate_future(db, revenue_change, expense_change, months)

@router.get("/ai-cfo")
def ai_cfo(db: Session = Depends(get_db)):
    return run_ai_cfo(db)

@router.get("/ask-cfo")
def ask_cfo(question: str = None, db: Session = Depends(get_db)):
    return run_llm_cfo(db, question)

@router.post("/generate-snapshot")
def create_snapshot(db: Session = Depends(get_db)):
    snap = generate_monthly_snapshot(db)
    return {
        "month": snap.month,
        "revenue": snap.total_revenue,
        "expense": snap.total_expense,
        "profit": snap.profit,
        "cash_balance": snap.cash_balance
    }
    
@router.get("/fraud-trend")
def fraud_trend(db: Session = Depends(get_db)):
    return get_fraud_trend(db)

@router.get("/vendor-risk")
def vendor_risk(db: Session = Depends(get_db)):
    return calculate_vendor_risk(db)

@router.get("/department-risk")
def department_risk(db: Session = Depends(get_db)):
    return calculate_department_risk(db)

@router.get("/company-health")
def company_health(db: Session = Depends(get_db)):
    return calculate_company_health(db)

@router.get("/ai-cfo-v2")
def ai_cfo_v2(db: Session = Depends(get_db)):
    return run_ai_cfo_v2(db)

@router.get("/bankruptcy-risk")
def bankruptcy_risk(db: Session = Depends(get_db)):
    return calculate_bankruptcy_risk(db)

@router.get("/strategy-simulate")
def strategy_simulate(
    revenue_change: float = 0,
    expense_change: float = 0,
    months: int = 6,
    db: Session = Depends(get_db)
):
    return run_strategy_simulation(
        db,
        revenue_change,
        expense_change,
        months
    )
    
@router.get("/ai-cfo-report")
def ai_cfo_report(db: Session = Depends(get_db)):
    return generate_cfo_report(db)

@router.get("/autonomous-cfo")
def autonomous_cfo(db: Session = Depends(get_db)):
    return run_autonomous_cfo_agent(db)

@router.get("/optimize-strategy")
def optimize_strategy(db: Session = Depends(get_db)):
    return run_strategy_optimizer(db)

@router.get("/revenue-momentum")
def revenue_momentum(db: Session = Depends(get_db)):
    return calculate_revenue_momentum(db)

@router.post("/setup-company")
def setup_company(
    company_name: str,
    bank_balance: float,
    monthly_revenue: float,
    monthly_expense: float,
    num_employees: int,
    avg_salary: float,
    db: Session = Depends(get_db)
):
    from app.services.ledger_service import create_transaction
    from app.models.finance_models import FinancialSnapshot
    from app.models.company_models import Employee, Expense
    from app.models.fraud_models import FraudScore
    from app.models.bankruptcy_model import BankruptcyRisk
    from app.models.company_health import CompanyHealth
    from datetime import date

    # Clear all data in correct order
    db.query(FraudScore).delete()
    db.query(Expense).delete()
    db.query(Transaction).delete()
    db.query(FinancialSnapshot).delete()
    db.query(CompanyHealth).delete()
    db.query(BankruptcyRisk).delete()
    db.query(Employee).delete()
    db.commit()

    # 2 — Set starting bank balance as owner equity (not revenue)
    # Directly set bank account balance without touching revenue
    opening_txn = Transaction(
        description="Opening balance - owner equity",
        amount=bank_balance,
        debit_account_id=1,   # Bank
        credit_account_id=6   # Owner Equity ← not revenue
    )
    db.add(opening_txn)
    db.commit()

    # 3 — Create employees
    for i in range(num_employees):
        emp = Employee(
            name=f"Employee {i+1}",
            salary=avg_salary,
            status="active"
        )
        db.add(emp)
    db.commit()

    # 4 — Create first snapshot
    snapshot = FinancialSnapshot(
        month=date.today().replace(day=1),
        total_revenue=bank_balance,
        total_expense=0,
        profit=bank_balance,
        cash_balance=bank_balance
    )
    db.add(snapshot)
    db.commit()

    return {
        "message": "Company setup complete",
        "company_name": company_name,
        "bank_balance": bank_balance,
        "employees_created": num_employees
    }