import streamlit as st
import pandas as pd
from datetime import date
import requests

st.set_page_config(page_title="FynMate Dashboard", layout="wide")

headers = {
        "x-api-key": st.secrets["API_KEY"],
        "Content-Type": "application/json"
    }

def fetch_transactions():
    try:
        r = requests.get(st.secrets["API_URL"]+"/transactions", headers=headers)
        data = r.json()
        if data["status"] == "success":
            return pd.DataFrame(data["data"])
        else:
            st.error("Gagal fetch data dari API")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Gagal fetch data dari API: {e}")
        return pd.DataFrame()

df = fetch_transactions()
df = df[["id", "message", "payment_method", "amount", "category", "created_at"]]

df["amount"] = pd.to_numeric(df["amount"])
df["amount"] = df["amount"].apply(lambda x: f"Rp {x:,.0f}").str.replace(',', '.').astype(str)

df["created_at"] = pd.to_datetime(df["created_at"], format="ISO8601")
df["created_at"] = pd.to_datetime(df["created_at"]).dt.strftime("%d-%m-%Y %H:%M")

total = df['amount'].str.replace('Rp ', '').str.replace('.', '').astype(float).sum()

df = df.rename(columns={
    "id": "ID",
    "message": "Transaction",
    "payment_method": "Payment Method",
    "amount": "Amount",
    "category": "Category",
    "created_at": "Created At"
})

st.title("FynMate Dashboard")
st.subheader("Lihat dan analisis pengeluaran kamu di sini 💸")

# r = requests.get(st.secrets["API_URL"]+"/transactions", headers=headers)
# data = r.json()
# st.write("Raw data from Supabase:", data)
# st.write(st.secrets)

# === Summary Metrics ===
st.dataframe(df)


# === Pagination ===
# items_per_page = 10
# if "page" not in st.session_state:
#     st.session_state.page = 0

# total_pages = (len(df) - 1) // items_per_page + 1

# col1, col2, col3 = st.columns(3)
# with col1:
#     if st.button("< Prev") and st.session_state.page > 0:
#         st.session_state.page -= 1

# with col2:
#     st.write(f"Page {st.session_state.page + 1} of {total_pages}")

# with col3:
#     if st.button("Next >") and st.session_state.page < total_pages - 1:
#         st.session_state.page += 1

# start = st.session_state.page * items_per_page
# end = start + items_per_page
# # st.dataframe(df.iloc[start:end])
# df.index = range(1, len(df) + 1)
# st.dataframe(df.iloc[start:end])



st.metric("Total pengeluaran bulan ini", f"Rp {total:,.0f}")

st.divider()
# #  === Summary pengeluaran hari ini ===
st.subheader(f"Pengeluaran Hari Ini ({date.today().strftime('%d-%m-%Y')})")

df["Created At"] = pd.to_datetime(df["Created At"])
today = pd.Timestamp.today().normalize()
df_today = df[df["Created At"].dt.date == today.date()]

st.dataframe(df_today)

total_today = df_today['amount'].sum()
st.metric("Total Pengeluaran Hari Ini: ", f"Rp {total_today:,.0f}")


st.divider()
#  === Chart Pengeluaran per Kategori ===
st.subheader("Pengeluaran per Kategori")
chart = df.groupby('Category')['amount'].sum().reset_index()
st.bar_chart(data=chart, x='Category', y='amount',)

st.warning("More to come! Please stay tuned", icon="⚠️")
