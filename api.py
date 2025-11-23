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
def get_transactions():
    try:
        result = supabase.table("transactions").select("*").order("created_at", desc=True).execute()
        return {
            "status": "success",
            "data": result.data
            }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/transactions/today")
def get_transactions_today():
    today = datetime.now().date().isoformat()

    try:
        result = (
            supabase.table("transactions")
            .select("*")
            .gte("created_at", f"{today} 00:00:00")
            .lte("created_at", f"{today} 23:59:59")
            .order("created_at", desc=True)
            .execute()
        )
        return {
            "status": "success",
            "data": result.data
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
