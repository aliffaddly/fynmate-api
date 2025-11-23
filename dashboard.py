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

st.title("FynMate Dashboard")
st.subheader("Lihat dan analisis pengeluaran lo di sini!")

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


# total = df['Amount'].sum()
# st.metric("Total Pengeluaran", f"Rp {total:,.0f}")


# #  === Summary pengeluaran hari ini ===
# st.subheader(f"Pengeluaran Hari Ini ({date.today()})")

# df["Date"] = pd.to_datetime(df["Date"])
# today = pd.Timestamp.today().normalize()
# df_today = df[df["Date"].dt.date == today.date()]

# total_today = df_today['Amount'].sum()
# st.metric("Total Pengeluaran Hari Ini: ", f"Rp {total_today:,.0f}")

# st.dataframe(df_today)


# #  === Chart Pengeluaran per Kategori ===
# st.subheader("Pengeluaran per Kategori")
# chart = df.groupby('Category')['Amount'].sum().reset_index()
# st.bar_chart(data=chart, x='Category', y='Amount',)

