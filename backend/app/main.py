from fastapi import FastAPI
from app.database import engine, Base, SessionLocal
from app.models import finance_models, company_models, fraud_models
from app.api.finance_api import router as finance_router
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(finance_router)

@app.on_event("startup")
def seed_accounts():
    db = SessionLocal()
    try:
        from app.models.finance_models import Account
        existing = db.query(Account).count()
        if existing == 0:
            accounts = [
                Account(id=1, name="Bank",           type="asset",   account_type="ASSET"),
                Account(id=2, name="Salary Expense", type="expense",  account_type="EXPENSE"),
                Account(id=3, name="Revenue",        type="revenue",  account_type="REVENUE"),
                Account(id=4, name="Vendor Expense", type="expense",  account_type="EXPENSE"),
                Account(id=6, name="Owner Equity",   type="equity",   account_type="EQUITY"),
            ]
            db.add_all(accounts)
            db.commit()
            print("✅ Accounts seeded successfully")
        else:
            print(f"✅ Accounts already exist ({existing} found)")
    except Exception as e:
        print(f"❌ Account seeding failed: {e}")
        db.rollback()
    finally:
        db.close()

@app.get("/")
def root():
    return {"message": "FinPilot backend running"}