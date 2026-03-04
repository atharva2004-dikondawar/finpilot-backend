import random
from datetime import date, timedelta
from sqlalchemy.orm import Session
from app.models.finance_models import FinancialSnapshot, Transaction, Account
from app.models.company_models import Employee, Vendor, Expense
from app.services.ledger_service import generate_monthly_snapshot, get_account_balance


# Helper: Simulate Revenue
def generate_monthly_revenue(db: Session, base_revenue: float):
    growth_factor = random.uniform(0.95, 1.10)  # small growth or drop
    revenue = base_revenue * growth_factor

    txn = Transaction(
        description="Monthly revenue",
        amount=revenue,
        debit_account_id=1,   # Bank
        credit_account_id=3   # Revenue
    )
    db.add(txn)

    return revenue

# Helper: Payroll
def run_payroll(db: Session):
    employees = db.query(Employee).filter(Employee.status == "active").all()

    total_payroll = 0

    for emp in employees:
        txn = Transaction(
            description=f"Salary paid to {emp.name}",
            amount=emp.salary,
            debit_account_id=2,  # Salary Expense
            credit_account_id=1  # Bank
        )
        db.add(txn)
        total_payroll += emp.salary

    return total_payroll

# Helper: Vendor Expenses
def generate_vendor_expenses(db: Session):
    vendors = db.query(Vendor).all()
    total_expense = 0

    for vendor in vendors:
        if random.random() < 0.6:  # 60% chance vendor billed this month
            amount = random.randint(10000, 80000)

            expense = Expense(
                vendor_id=vendor.id,
                department_id=random.randint(1, 5),
                amount=amount,
                description=f"Monthly payment to {vendor.name}",
                date=date.today()
            )
            db.add(expense)

            txn = Transaction(
                description=f"Vendor payment: {vendor.name}",
                amount=amount,
                debit_account_id=4,  # Vendor Expense
                credit_account_id=1  # Bank
            )
            db.add(txn)

            total_expense += amount

    return total_expense

# MAIN GENERATOR
from datetime import datetime

def generate_company_history(db: Session, months: int = 24, base_revenue: float = 3000000):
    from app.models.finance_models import FinancialSnapshot, Transaction
    from app.models.company_models import Expense
    from app.models.fraud_models import FraudScore

    # Auto-clean before generating to avoid UniqueViolation
    db.query(FraudScore).delete()
    db.query(Expense).delete()
    db.query(Transaction).delete()
    db.query(FinancialSnapshot).delete()
    db.commit()

    current_revenue = base_revenue
    today = date.today().replace(day=1)

    for i in range(months):

        # Simulate past months properly
        simulated_month = today - timedelta(days=30 * (months - i))

        print(f"Generating data for {simulated_month}")

        # 1️⃣ Revenue
        current_revenue = generate_monthly_revenue(db, current_revenue)

        # 2️⃣ Payroll
        run_payroll(db)

        # 3️⃣ Vendor Expenses
        generate_vendor_expenses(db)

        db.commit()

        # 4️⃣ Create Snapshot manually for that month
        revenue_accounts = db.query(Account).filter(Account.account_type == "REVENUE").all()
        expense_accounts = db.query(Account).filter(Account.account_type == "EXPENSE").all()

        total_revenue = sum(get_account_balance(db, acc.id) for acc in revenue_accounts)
        total_expense = sum(get_account_balance(db, acc.id) for acc in expense_accounts)
        cash_balance = get_account_balance(db, 1)  # Bank account balance

        snapshot = FinancialSnapshot(
            month=simulated_month,
            total_revenue=total_revenue,
            total_expense=total_expense,
            profit=total_revenue - total_expense,
            cash_balance=cash_balance
        )

        db.add(snapshot)
        db.commit()

    # ✅ OUTSIDE the loop — runs once after ALL months generated
    try:
        from app.services.fraud_engine import run_fraud_detection
        run_fraud_detection(db)
        print("Fraud detection completed after history generation")
    except Exception as e:
        print(f"Fraud detection skipped: {e}")

    return {"message": f"{months} months financial history generated"}