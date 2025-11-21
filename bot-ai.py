from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from dotenv import load_dotenv
import os
from datetime import datetime
from openai import OpenAI
import requests


# Load token from env
load_dotenv("env.local")  # test local
# load_dotenv("env.prod") # for deploy

TOKEN = os.getenv("TG_TOKEN")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
API_URL = os.getenv("API_URL")
API_KEY = os.getenv("API_KEY")

# parse with AI
def parse_with_ai(text):
    prompt = f"""
    You are a finance assistant that extracts structured data from messages.
    You understand Indonesian language, including slang and abbreviations. 
    Message: "{text}"
    Output JSON with keys: category, amount, note, payment and date (YYYY-MM-DD hh:mm:ss).
    If amount not found, return null.

    Category for expenses only, choose from: Food, Transport, Entertainment, Shopping, Bills, Amal/Donasi/Zakat, Self Care, Other.
    Elaborate note if needed using Indonesian. make it concise and relevant to the message. remove unnecessary words, amount, and period at the end.
    Exclude any words that indicate buying or spending from the note e.g "beli", "makan", "ngopi", "jajan", "bayar", etc.
    Payment method: Cash, OVO, GoPay, Dana, Shopeepay, Credit Card, BCA, Mandiri, Jago, or any payment methods that users input upon 'via'. If not found, return "Other".
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object" }
        )
        result = response.choices[0].message.content
        import json
        return json.loads(result)
    except Exception as e:
        print("Error parsing with AI:", e)
        return None

# Save transaction to API
def save_to_api(user_id, username, note, category, amount, payment_method, created_at):
    payload = {
        "user_id": user_id,
        "username": username,
        "message": note,
        "category": category,
        "amount": amount,
        "payment_method": payment_method,
        "created_at": created_at
    }

    headers = {
        "x-api-key": API_KEY,
        "Content-Type": "application/json"
    }

    try:
        r = requests.post(API_URL+"/transactions", json=payload, headers=headers)
        print("API response:", r.json())
        return True
    except Exception as e:
        print("Gagal POST ke API:", e)
        return False


# Command /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    await update.message.reply_text(
        f"Hi {user.first_name}! 👋 Kirim aja pesan kayak 'makan siang 50k' buat nyatet pengeluaran 💸"
    )

# Handler buat teks biasa (bukan command)
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user = update.message.from_user

    data = parse_with_ai(text)
    if not data or not data.get("amount"):
        await update.message.reply_text(
            "Oops! Nominal gak ketemu nih😅\nCoba ketik kayak 'ngopi 20k' atau 'beli boba 25000'.")
    else:
        amount = int(data.get("amount", 0))
        category = data.get("category", "Other")
        note = data.get("note", text)
        payment_method = data.get("payment", "Other")
        created_at_now = datetime.now().strftime("%Y-%m-%d %H:%M")

        save_to_api(user.id, user.username, note, category, amount, payment_method, created_at_now)

        await update.message.reply_text(
            f"<b>✅ Noted bro, pengeluaran lo:</b>\n"
            f"<b>Deskripsi:</b> {note}\n"
            f"<b>Nominal:</b> Rp {amount:,.0f}\n"
            f"<b>Metode Pembayaran:</b> {payment_method}\n"
            f"<b>Kategori:</b> {category}\n"
            f"<b>Tanggal:</b> {created_at_now}",
            parse_mode="HTML"
        )

# Main
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    # Command /start
    app.add_handler(CommandHandler("start", start))

    # Pesan biasa
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot jalan bro... 🚀 (Ctrl + C buat stop)")
    app.run_polling()