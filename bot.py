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

# Load token dari .env
load_dotenv()
TOKEN = os.getenv("TG_TOKEN")

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

    amount = parse_amount(text)
    if amount:
        category = "Other"

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Simpan ke database
        cursor.execute("INSERT INTO transactions (user_id, username, message, category, amount, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                       (user.id, user.username, text, category, amount, now))
        conn.commit()

        await update.message.reply_text(
            f"Noted bro 💸, pengeluaran lo: Rp {amount:,.0f}\n"
            f"Kategori: {category}\n"
            f"🕒 {now}"
        )
    else:
        await update.message.reply_text(
            "Gue gak nemu nominalnya bro 😅\nCoba ketik kayak 'ngopi 20k' atau 'beli boba 25000'."
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