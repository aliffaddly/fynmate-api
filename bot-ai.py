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
import re
import sqlite3
from datetime import datetime
from openai import OpenAI
import requests

# Load token dari .env
load_dotenv()
TOKEN = os.getenv("TG_TOKEN")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# Setup database SQLite
DB_PATH = "db/finance.db"
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Create table kalau belum ada
cursor.execute("""
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    username TEXT,
    message TEXT,
    category TEXT,
    amount INTEGER,
    payment_method TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")
conn.commit()

# === Helper: parse nominal dari text ===
def parse_amount(text):
    match = re.search(r"(\d+(?:[.,]?\d+)?)(k|rb)?", text.lower())
    if not match:
        return None

    num = match.group(1)
    suffix = match.group(2)

    # normalize angka
    num = num.replace(",", ".")
    amount = float(num)

    if suffix == "k" or suffix == "rb":
        amount *= 1000

    return int(amount)

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
    Payment method: Cash, OVO, GoPay, Dana, Credit Card DBS, Credit Card BRI, BCA, Mandiri, Jago, Other. If not found, return "Other".
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

# Command /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    await update.message.reply_text(
        f"Yo {user.first_name}! 👋 Kirim aja pesan kayak 'makan siang 50k' buat nyatet pengeluaran 💸"
    )

# Handler buat teks biasa (bukan command)
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user = update.message.from_user

    data = parse_with_ai(text)
    if not data or not data.get("amount"):
        # fallback pakai regex
        amount = parse_amount(text)
        if not amount:
            await update.message.reply_text(
                "Gue gak nemu nominalnya bro 😅\nCoba ketik kayak 'ngopi 20k' atau 'beli boba 25000'."
            )
            return
        category = "Other"
        note = text
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
    else:
        amount = int(data.get("amount", 0))
        category = data.get("category", "Other")
        note = data.get("note", text)
        payment = data.get("payment", "Other")
        now = datetime.now().strftime("%Y-%m-%d %H:%M")

        # Simpan ke database
        cursor.execute("INSERT INTO transactions (user_id, username, message, category, amount, payment_method, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                       (user.id, user.username, note, category, amount, payment, now))
        conn.commit()

        await update.message.reply_text(
            f"<b>✅ Noted bro, pengeluaran lo:</b>\n"
            f"<b>Deskripsi:</b> {note}\n"
            f"<b>Nominal:</b> Rp {amount:,.0f}\n"
            f"<b>Metode Pembayaran:</b> {payment}\n"
            f"<b>Kategori:</b> {category}\n"
            f"<b>Tanggal:</b> {now}",
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