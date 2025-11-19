from fastapi import FastAPI
import sqlite3
from datetime import datetime
import pandas as pd


app = FastAPI()

DB_PATH = "db/finance.db"

def get_db():
    return sqlite3.connect(DB_PATH)

@app.get("/transactions/")
def get_transactions():
    conn = get_db()
    df = pd.read_sql_query("SELECT * FROM transactions ORDER BY created_at DESC", conn)
    conn.close()
    return df.to_dict(orient="records")

@app.get("/transactions/today")
def get_transactions_today():
    today = datetime.now().strftime("%Y-%m-%d %H:%M")
    conn = get_db()
    df = pd.read_sql_query(f"SELECT * FROM transactions WHERE DATE(created_at) = '{today}' ORDER BY created_at DESC", conn)
    conn.close()
    return df.to_dict(orient="records")

@app.post("/transactions/")
def add_transaction(user_id: int, username: str, note: str, category: str, amount: int, payment_method: str, created_at: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO transactions (user_id, username, message, category, amount, payment_method, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                       (user_id, username, note, category, amount, payment_method, created_at))
    conn.commit()
    conn.close()
    return {
        "status": "success",
        "message": "Transaction added successfully",
        "saved": {
            "user_id": user_id,
            "username": username,
            "message": note,
            "category": category,
            "amount": amount,
            "created_at": created_at
        }
    }