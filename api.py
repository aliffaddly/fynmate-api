from fastapi import FastAPI, Body, Header, HTTPException
from datetime import datetime
import pandas as pd
import os
from dotenv import load_dotenv
from supabase import create_client, Client

app = FastAPI()

# load_dotenv("env.local")
load_dotenv("env.prod")

url: str = os.getenv("SUPABASE_URL")
key: str = os.getenv("SUPABASE_KEY")

# Connect to Supabase
supabase: Client = create_client(url, key)

@app.get("/transactions")
def get_transactions(uid: int):
    try:
        result = supabase.table("transactions").select("*").eq("user_id", uid).order("created_at", desc=True).execute()
        total_expense = sum(item["amount"] for item in result.data)
        
        if not result.data:
            return {
                "status": "error",
                "message": "User not found or no transactions yet",
                "data": []
            }
        
        return {
            "status": "success",
            "data": result.data,
            "total_expense": total_expense,
            "count": len(result.data)
            }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/transactions/today")
def get_transactions_today(uid: int):
    today = datetime.now().date().isoformat()

    try:
        result = (
            supabase.table("transactions")
            .select("*")
            .eq("user_id", uid)
            .gte("created_at", f"{today} 00:00:00")
            .lte("created_at", f"{today} 23:59:59")
            .order("created_at", desc=True)
            .execute()
        )
        total_expense_today = sum(item["amount"] for item in result.data)
        if not result.data:
            return {
                "status": "error",
                "message": "No transaction found for today",
                "data": []
            }

        return {
            "status": "success",
            "data": result.data,
            "total_expense_today": total_expense_today,
            "count": len(result.data)
            }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/transactions")
def add_transaction(
    user_id: int = Body(...), 
    username: str = Body(...), 
    message: str = Body(...), 
    category: str = Body(...), 
    amount: int = Body(...), 
    payment_method: str = Body(...), 
    created_at: str = Body(None)
):
    
    data = {
        "user_id": user_id,
        "username": username,
        "message": message,
        "category": category,
        "amount": amount,
        "payment_method": payment_method,
        "created_at": created_at
    }

    try:
        result = supabase.table("transactions").insert(data).execute()
        return {
            "status": "success",
            "message": "Transaction added successfully",
            "data": result.data
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
