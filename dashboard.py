import streamlit as st
import pandas as pd
from datetime import date, datetime
import requests
import plotly.express as px
import calendar
from dateutil.relativedelta import relativedelta

# Get user id from URL params
query_params = st.query_params
user_id = query_params.get("uid", [None])
if isinstance(user_id, list):
    user_id = user_id[0]
if user_id is None or user_id == "":
    st.error("No UID provided.", icon="🚨")
    st.stop()

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

st.set_page_config(page_title="FynMate Dashboard", layout="wide")
st.title("FynMate Dashboard")
st.subheader("Lihat dan analisis pengeluaran kamu di sini 💸")
st.divider()


df, total_expense, count = fetch_transactions()
df = df[["id", "message", "payment_method", "amount", "category", "created_at"]]

df["amount"] = df["amount"].astype(int)
df["amount_display"] = df["amount"].apply(lambda x: f"Rp {x:,.0f}").str.replace(',', '.')

df["created_at"] = pd.to_datetime(df["created_at"], format="ISO8601")
df["created_at_display"] = pd.to_datetime(df["created_at"]).dt.strftime("%d-%m-%Y %H:%M")

# === Dropdwon filter by month ===
# Generate last 6 months
now = datetime.now()
last_months = []
for i in range(0,6):
    dt = now - relativedelta(months=i)
    last_months.append((dt.year, dt.month))

# month options for dropdown
month_options = [
    f"{calendar.month_name[m]} {y}" for (y, m) in last_months
]

# Set default to current month
col1,col2 = st.columns([1,5])
with col1:
    default_label = f"{calendar.month_name[now.month]} {now.year}"
    selected_label = st.selectbox("Filter berdasarkan bulan:",month_options, index=0)

# Filter dataframe based on selected month
selected_month_name, selected_year = selected_label.split(" ")
selected_year = int(selected_year)
selected_month = list(calendar.month_name).index(selected_month_name)
df_filtered = df[
    (df["created_at"].dt.month == selected_month) &
    (df["created_at"].dt.year == selected_year)
]

# Monthly total expense
monthly_expense = df_filtered["amount"].sum()

df_display = df_filtered.rename(columns={
    # "id": "ID",
    "message": "Transaction",
    "payment_method": "Payment Method",
    "amount_display": "Amount",
    "category": "Category",
    "created_at_display": "Created At"
})[[
    # "ID",
    "Transaction",
    "Payment Method",
    "Amount",     
    "Category",
    "Created At"
]]

# r = requests.get(st.secrets["API_URL"]+"/transactions", headers=headers)
# data = r.json()
# st.write("Raw data from Supabase:", data)

# === Summary Metrics ===
df_display.index = range(1, len(df_display) + 1)
st.subheader(f"Pengeluaran Kamu di Bulan {selected_month_name} {selected_year}")
st.dataframe(df_display)

st.metric(f"Total pengeluaran bulan {selected_month_name} {selected_year}", f"Rp {monthly_expense:,.0f}".replace(',', '.'))
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

# #  === Chart Pengeluaran per Kategori ===
st.subheader(f"Pengeluaran per Kategori {selected_month_name} {selected_year}")

chart = (df_filtered.groupby('category')['amount'].sum().sort_values(ascending=False).reset_index())

fig_bar = px.bar(chart, x='category', y='amount', labels={'x': 'Category', 'y': 'Amount'})
fig_pie = px.pie(chart, names='category', values='amount')

cola,colb = st.columns(2)
with cola:
    st.plotly_chart(fig_bar, use_container_width=True)
with colb:
    st.plotly_chart(fig_pie, use_container_width=True)

st.divider()
# #  === Summary pengeluaran hari ini ===
st.subheader(f"Pengeluaran Hari Ini ({date.today().strftime('%d %b %Y')})")

result = fetch_transactions_today()
if isinstance(result, tuple) and len(result) == 3:
    df_today, total_expense_today, count = result
    if df_today.empty:
        pass
    else:   
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



st.warning("More to come! Please stay tuned", icon="😁")
