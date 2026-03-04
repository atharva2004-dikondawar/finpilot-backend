import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sqlalchemy.orm import Session
from sklearn.preprocessing import StandardScaler
from app.models.finance_models import Transaction
from app.models.fraud_models import FraudScore


def extract_features(transactions):
    rows = []

    # Sort by time
    # transactions = sorted(transactions, key=lambda x: x.created_at)

    amounts = [txn.amount for txn in transactions]
    mean_amt = np.mean(amounts)
    std_amt = np.std(amounts) if np.std(amounts) > 0 else 1

    prev_time = None

    for txn in transactions:
        amount = txn.amount
        log_amount = np.log1p(amount)
        z_score = (amount - mean_amt) / std_amt

        # --- Time gap feature ---
        if prev_time is None:
            time_gap = 0
        else:
            delta = txn.created_at - prev_time
            time_gap = np.log1p(delta.total_seconds())

        prev_time = txn.created_at

        account_pattern = txn.debit_account_id * 10 + txn.credit_account_id

        rows.append([
            amount,
            log_amount,
            z_score,
            txn.debit_account_id,
            txn.credit_account_id,
            account_pattern,
            time_gap
        ])

    return np.array(rows)

def run_fraud_detection(db: Session):
    transactions = db.query(Transaction).order_by(Transaction.created_at).all()

    if len(transactions) < 10:
        return {"message": "Not enough data for fraud detection"}

    X = extract_features(transactions)
    scaler = StandardScaler()
    X = scaler.fit_transform(X)
    
    model = IsolationForest(
        n_estimators=200,
        contamination=0.08,
        random_state=42
    )
    model.fit(X)

    raw_scores = model.decision_function(X)

    # Convert to probability-like risk (0-100)
    min_s, max_s = raw_scores.min(), raw_scores.max()
    scores = 100 * (max_s - raw_scores) / (max_s - min_s + 1e-6)

    # Clear old scores
    db.query(FraudScore).delete()
    
    amounts = [txn.amount for txn in transactions]
    mean_amt = np.mean(amounts)
    std_amt = np.std(amounts) if np.std(amounts) > 0 else 1
    spike_ids = detect_spending_spike(transactions)

    for i, (txn, score) in enumerate(zip(transactions, scores)):

        explanation = explain_transaction(txn, mean_amt, std_amt)

        if txn.id in spike_ids:
            explanation += "; Sudden abnormal spending spike"

        if score > 80:
            explanation += "; High anomaly risk detected by model"

        fraud = FraudScore(
            transaction_id=txn.id,
            score=float(score),
            explanation=explanation
        )

        db.add(fraud)
    db.commit()

    return {"message": "Fraud detection completed"}

def explain_transaction(txn, mean_amt, std_amt):
    reasons = []

    amount = txn.amount

    # Z-score
    z = (amount - mean_amt) / std_amt if std_amt > 0 else 0

    if abs(z) > 2:
        reasons.append(f"Amount is {round(abs(z),2)} std deviations from normal")

    # Large amount ratio
    if amount > mean_amt * 2:
        ratio = amount / mean_amt if mean_amt > 0 else 0
        reasons.append(f"Amount is {round(ratio,2)}x higher than average")

    # Unusual account movement
    if txn.debit_account_id == txn.credit_account_id:
        reasons.append("Same debit & credit account pattern")

    if not reasons:
        reasons.append("Unusual behavior detected by ML model")

    return "; ".join(reasons)

def detect_spending_spike(transactions):
    amounts = [txn.amount for txn in transactions]

    if len(amounts) < 5:
        return []

    mean_amt = np.mean(amounts)
    spike_txns = []

    for txn in transactions:
        if txn.amount > mean_amt * 3:
            spike_txns.append(txn.id)

    return spike_txns

def get_fraud_trend(db):
    total = db.query(FraudScore).count()
    high_risk = db.query(FraudScore).filter(FraudScore.score > 70).count()

    rate = (high_risk / total) if total > 0 else 0

    return {
        "total_transactions_scored": total,
        "high_risk_transactions": high_risk,
        "fraud_rate": rate
    }