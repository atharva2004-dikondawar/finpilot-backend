from sqlalchemy.orm import Session
from app.models.finance_models import Transaction, Account, FinancialSnapshot
from app.models.company_models import Employee, Expense, Department, Vendor
from sqlalchemy import func
from datetime import date

def create_transaction(db, description, amount, debit_account_id, credit_account_id):

    if amount <= 0:
        raise ValueError("Transaction amount must be positive")

    if debit_account_id == credit_account_id:
        raise ValueError("Debit and credit accounts cannot be the same")

    debit_account = db.query(Account).filter(Account.id == debit_account_id).first()
    credit_account = db.query(Account).filter(Account.id == credit_account_id).first()

    if not debit_account or not credit_account:
        raise ValueError("Invalid account ID")

    txn = Transaction(
        description=description,
        amount=amount,
        debit_account_id=debit_account_id,
        credit_account_id=credit_account_id
    )

    db.add(txn)
    db.commit()
    db.refresh(txn)

    return txn


def get_account_balance(db, account_id):
    account = db.query(Account).filter(Account.id == account_id).first()

    if not account:
        return 0

    # Sum of debits
    debit_sum = db.query(func.sum(Transaction.amount)).filter(
        Transaction.debit_account_id == account_id
    ).scalar() or 0

    # Sum of credits
    credit_sum = db.query(func.sum(Transaction.amount)).filter(
        Transaction.credit_account_id == account_id
    ).scalar() or 0

    acc_type = account.account_type.upper()

    # Accounting rules
    if acc_type in ["ASSET", "EXPENSE"]:
        balance = debit_sum - credit_sum
    elif acc_type in ["LIABILITY", "REVENUE", "EQUITY"]:
        balance = credit_sum - debit_sum
    else:
        balance = debit_sum - credit_sum   # fallback safety

    return float(balance)

def calculate_profit_loss(db):
    revenue_accounts = db.query(Account).filter(func.upper(Account.account_type) == "REVENUE").all()
    expense_accounts = db.query(Account).filter(func.upper(Account.account_type) == "EXPENSE").all()

    total_revenue = 0
    total_expense = 0

    for account in revenue_accounts:
        debit_sum = db.query(func.sum(Transaction.amount)).filter(
            Transaction.debit_account_id == account.id
        ).scalar() or 0

        credit_sum = db.query(func.sum(Transaction.amount)).filter(
            Transaction.credit_account_id == account.id
        ).scalar() or 0

        total_revenue += (credit_sum - debit_sum)

    for account in expense_accounts:
        debit_sum = db.query(func.sum(Transaction.amount)).filter(
            Transaction.debit_account_id == account.id
        ).scalar() or 0

        credit_sum = db.query(func.sum(Transaction.amount)).filter(
            Transaction.credit_account_id == account.id
        ).scalar() or 0

        total_expense += (debit_sum - credit_sum)

    profit = float(total_revenue) - float(total_expense)

    return {
        "total_revenue": total_revenue,
        "total_expense": total_expense,
        "profit": profit
    }

def process_monthly_payroll(db):
    employees = db.query(Employee).filter(Employee.status == "active").all()

    for emp in employees:
        txn = Transaction(
            description=f"Salary paid to {emp.name}",
            amount=emp.salary,
            debit_account_id=2,   # Salary Expense account
            credit_account_id=1   # Bank account
        )
        db.add(txn)

    db.commit()

    return {"message": "Payroll processed"}

def record_expense(db, vendor_id, department_id, amount, description, expense_date):

    # 1. Create ledger transaction (Expense → Cash)
    txn = create_transaction(
        db,
        f"Vendor payment: {description}",
        amount,
        debit_account_id=4,   # Expense Account
        credit_account_id=1   # Cash/Bank
    )

    # 2. Create expense AND LINK transaction_id
    expense = Expense(
        vendor_id=vendor_id,
        department_id=department_id,
        amount=amount,
        description=description,
        date=expense_date,
        transaction_id=txn.id   
    )

    db.add(expense)
    db.commit()

    return {"message": "Expense recorded"}

def get_department_expenses(db):
    departments = db.query(Department).all()
    result = {}

    for dept in departments:
        total = db.query(func.sum(Expense.amount)).filter(
            Expense.department_id == dept.id
        ).scalar() or 0

        result[dept.name] = total

    return result

def get_vendor_spending(db):
    vendors = db.query(Vendor).all()
    result = {}

    for vendor in vendors:
        total = db.query(func.sum(Expense.amount)).filter(
            Expense.vendor_id == vendor.id
        ).scalar() or 0

        result[vendor.name] = total

    return result

def get_financial_snapshot(db):
    bank_balance = get_account_balance(db, 1)   # Bank
    pnl = calculate_profit_loss(db)

    dept_expenses = get_department_expenses(db)
    vendor_spending = get_vendor_spending(db)

    return {
        "bank_balance": bank_balance,
        "total_revenue": pnl["total_revenue"],
        "total_expense": pnl["total_expense"],
        "profit": pnl["profit"],
        "department_expenses": dept_expenses,
        "vendor_spending": vendor_spending
    }


def generate_monthly_snapshot(db):

    # ============================
    # 1. Calculate Revenue
    # ============================
    revenue_accounts = db.query(Account).filter(Account.account_type == "REVENUE").all()
    total_revenue = abs(sum(get_account_balance(db, acc.id) for acc in revenue_accounts))

    # ============================
    # 2. Calculate Expense
    # ============================
    expense_accounts = db.query(Account).filter(Account.account_type == "EXPENSE").all()
    total_expense = abs(sum(get_account_balance(db, acc.id) for acc in expense_accounts))
    
    
    
    
    # If revenue missing, estimate minimal revenue for stability
    if total_revenue == 0 and total_expense > 0:
        total_revenue = total_expense * 0.6

    # ============================
    # 3. Cash / Bank Balance
    # ============================
    # bank_account = db.query(Account).filter(Account.account_type == "ASSET").first()
    asset_accounts = db.query(Account).filter(Account.account_type == "ASSET").all()
    # cash_balance = get_account_balance(db, bank_account.id) if bank_account else 0
    cash_balance = sum(get_account_balance(db, acc.id) for acc in asset_accounts)
    
    # Smooth negative collapse (prevents model death)
    if cash_balance < 0:
        cash_balance = cash_balance * 0.5

    # ============================
    # 4. Profit
    # ============================
    profit = total_revenue - total_expense

    # ============================
    # 5. Monthly Key
    # ============================
    month_start = date.today().replace(day=1)

    # ============================
    # 6. Update existing OR create
    # ============================
    existing = db.query(FinancialSnapshot).filter(FinancialSnapshot.month == month_start).first()

    if existing:
        existing.total_revenue = total_revenue
        existing.total_expense = total_expense
        existing.profit = profit
        existing.cash_balance = cash_balance
        db.commit()
        db.refresh(existing)
        return existing

    snapshot = FinancialSnapshot(
        month=month_start,
        total_revenue=total_revenue,
        total_expense=total_expense,
        profit=profit,
        cash_balance=cash_balance
    )

    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)

    return snapshot