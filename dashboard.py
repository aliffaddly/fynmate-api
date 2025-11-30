import streamlit as st
import pandas as pd
from datetime import date
import requests
import plotly.express as px

# Get user id from URL params
query_params = st.query_params
user_id = query_params.get("uid", [None])
if isinstance(user_id, list):
    user_id = user_id[0]
if user_id is None or user_id == "":
    st.error("No UID provided.", icon="🚨")
    st.stop()

st.set_page_config(page_title="FynMate Dashboard", layout="wide")

headers = {
        "x-api-key": st.secrets["API_KEY"],
        "Content-Type": "application/json"
    }

def fetch_transactions():
    try:
        r = requests.get(st.secrets[f"API_URL"]+f"/transactions?uid={user_id}", headers=headers)
        # st.write("DEBUG URL:", st.secrets[f"API_URL"]+f"/transactions?uid={user_id}")
        data = r.json()
        if data["status"] == "success":
            return pd.DataFrame(data["data"]), data.get("total_expense"), data.get("count")
        if data["status"] != "success":
            err_msg = data.get("message")
            st.error(err_msg, icon="🚨")
            st.stop()
            # return pd.DataFrame()
    except Exception as e:
        st.error(f"Gagal fetch data dari API: {e}")
        # return pd.DataFrame()

def fetch_transactions_today():
    try:
        r = requests.get(st.secrets[f"API_URL"]+f"/transactions/today?uid={user_id}", headers=headers)
        data = r.json()
        if data["status"] == "success":
            return pd.DataFrame(data["data"]), data.get("total_expense_today"), data.get("count")
        if data["status"] != "success":
            msg = data.get("message")
            st.info(msg, icon="ℹ️")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Failed to fetch data from API: {e}")
        return pd.DataFrame()

df, total_expense, count = fetch_transactions()
df = df[["id", "message", "payment_method", "amount", "category", "created_at"]]

df["amount"] = df["amount"].astype(int)
df["amount_display"] = df["amount"].apply(lambda x: f"Rp {x:,.0f}").str.replace(',', '.')

df["created_at"] = pd.to_datetime(df["created_at"], format="ISO8601")
df["created_at"] = pd.to_datetime(df["created_at"]).dt.strftime("%d-%m-%Y %H:%M")

df_display = df.rename(columns={
    # "id": "ID",
    "message": "Transaction",
    "payment_method": "Payment Method",
    "amount_display": "Amount",
    "category": "Category",
    "created_at": "Created At"
})[[
    # "ID",
    "Transaction",
    "Payment Method",
    "Amount",     
    "Category",
    "Created At"
]]

st.title("FynMate Dashboard")
st.subheader("Lihat dan analisis pengeluaran kamu di sini 💸")

# r = requests.get(st.secrets["API_URL"]+"/transactions", headers=headers)
# data = r.json()
# st.write("Raw data from Supabase:", data)

# === Summary Metrics ===
df_display.index = range(1, len(df_display) + 1)
st.dataframe(df_display)

st.metric("Total pengeluaran bulan ini", f"Rp {total_expense:,.0f}".replace(',', '.'))
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

st.divider()

# #  === Summary pengeluaran hari ini ===
st.subheader(f"Pengeluaran Hari Ini ({date.today().strftime('%d %b %Y')})")

df_today = fetch_transactions_today()
if df_today.empty:
    pass
else:   
    df_today, total_expense_today, count = fetch_transactions_today()
    df_today["amount"] = df_today["amount"].astype(int)
    df_today["amount_display"] = df_today["amount"].apply(lambda x: f"Rp {x:,.0f}").str.replace(',', '.')
    df_today["created_at"] = pd.to_datetime(df_today["created_at"], format="ISO8601")
    df_today["created_at"] = pd.to_datetime(df_today["created_at"]).dt.strftime("%d-%m-%Y %H:%M")
    df_today = df_today.rename(columns={
        # "id": "ID",
        "message": "Transaction",
        "payment_method": "Payment Method",
        "amount_display": "Amount",
        "category": "Category",
        "created_at": "Created At"
    })[[
        # "ID",
        "Transaction",
        "Payment Method",
        "Amount",     
        "Category",
        "Created At"
    ]]
    df_today.index = range(1, len(df_today) + 1)
    st.dataframe(df_today)

    total_today = total_expense_today
    st.metric("Total Pengeluaran Hari Ini: ", f"Rp {total_today:,.0f}".replace(',', '.'))

st.divider()

# #  === Chart Pengeluaran per Kategori ===
st.subheader("Pengeluaran per Kategori")
chart = (df.groupby('category')['amount'].sum().sort_values(ascending=False).reset_index())

fig_bar = px.bar(chart, x='category', y='amount', labels={'x': 'Category', 'y': 'Amount'})
# fig_pie = px.pie(chart, names='category', values='amount', title='Proporsi Pengeluaran per Kategori')

st.plotly_chart(fig_bar, use_container_width=True)
# st.plotly_chart(fig_pie, use_container_width=True)

st.warning("More to come! Please stay tuned", icon="😁")
