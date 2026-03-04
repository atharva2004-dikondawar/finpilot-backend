from fastapi import FastAPI
from app.database import engine, Base
from app.models import finance_models, company_models, fraud_models
from app.api.finance_api import router as finance_router
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

Base.metadata.create_all(bind=engine)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],  # Vite default
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(finance_router)

@app.get("/")
def root():
    return {"message": "FinPilot backend running"}

