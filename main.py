import streamlit as st
import pandas as pd
import requests

# --- Indian number formatter ---
def format_inr(value):
    try:
        num = float(value)
        if num < 1e5:
            return f"{num:,.2f}"
        int_part, dec_part = str(f"{num:.2f}").split(".")
        last3 = int_part[-3:]
        rest = int_part[:-3]
        if rest != "":
            rest = ",".join([rest[max(i - 2, 0):i] for i in range(len(rest), 0, -2)][::-1])
            formatted = rest + "," + last3
        else:
            formatted = last3
        return f"₹ {formatted}.{dec_part}"
    except:
        return "₹ 0.00"

# --- Fetch data from CoinGecko API ---
@st.cache_data(ttl=300)
def load_data():
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "inr",
        "order": "volume_desc",
        "per_page": 250,
        "page": 1,
        "sparkline": "false",
        "locale": "en",
        "precision": 2,
        "price_change_percentage": "1h,24h,7d,14d,30d,200d,1y"
    }
    response = requests.get(url, params=params)
    return pd.DataFrame(response.json())

# --- Load Data ---
df = load_data()

# --- Set Streamlit layout ---
st.set_page_config(page_title="Crypto Filter", layout="wide")
st.title("🪙 Crypto Dashboard - CoinGecko INR")

# --- Sidebar Filters ---
st.sidebar.header("🔍 Multi-Level Filters")

# 1️⃣ Market Cap Rank ≤
if "market_cap_rank" in df.columns:
    max_rank = int(df["market_cap_rank"].dropna().max())
    rank_input = st.sidebar.number_input(
        "1️⃣ Market Cap Rank ≤", min_value=1, max_value=max_rank, value=max_rank
    )
    filtered_df = df[df["market_cap_rank"] <= rank_input].copy()
else:
    st.error("⚠️ 'market_cap_rank' column missing in API response.")
    st.stop()

# 2️⃣ Current Price ≥
price_min_input = st.sidebar.text_input("2️⃣ Current Price ≥ (INR)", "")
if price_min_input.strip():
    try:
        min_val = float(price_min_input.replace(",", ""))
        filtered_df = filtered_df[filtered_df["current_price"] >= min_val]
    except ValueError:
        st.sidebar.error("❌ Enter a valid number for min price")

# 3️⃣ Current Price ≤
price_max_input = st.sidebar.text_input("3️⃣ Current Price ≤ (INR)", "")
if price_max_input.strip():
    try:
        max_val = float(price_max_input.replace(",", ""))
        filtered_df = filtered_df[filtered_df["current_price"] <= max_val]
    except ValueError:
        st.sidebar.error("❌ Enter a valid number for max price")

# 4️⃣ Price Change Filters
def apply_pct_filter(df, column, label):
    option = st.sidebar.selectbox(f"{label} Price Change (%)", ["All", "Positive", "Negative"])
    if option == "Positive":
        return df[df[column] > 0]
    elif option == "Negative":
        return df[df[column] < 0]
    return df

filtered_df = apply_pct_filter(filtered_df, "price_change_percentage_1h_in_currency", "4️⃣ 1h")
filtered_df = apply_pct_filter(filtered_df, "price_change_percentage_24h_in_currency", "5️⃣ 24h")
filtered_df = apply_pct_filter(filtered_df, "price_change_percentage_7d_in_currency", "6️⃣ 7d")
filtered_df = apply_pct_filter(filtered_df, "price_change_percentage_14d_in_currency", "7️⃣ 14d")
filtered_df = apply_pct_filter(filtered_df, "price_change_percentage_30d_in_currency", "8️⃣ 30d")
filtered_df = apply_pct_filter(filtered_df, "price_change_percentage_200d_in_currency", "9️⃣ 200d")
filtered_df = apply_pct_filter(filtered_df, "price_change_percentage_1y_in_currency", "🔟 1y")
filtered_df = apply_pct_filter(filtered_df, "market_cap_change_percentage_24h", "🧮 MCap 24h")

# --- Format numbers safely ---
filtered_df = filtered_df.copy()
filtered_df["formatted_price"] = filtered_df["current_price"].apply(format_inr)
filtered_df["formatted_market_cap"] = filtered_df["market_cap"].apply(format_inr)

# --- Show Data ---
st.subheader(f"📊 Showing {len(filtered_df)} coins")
st.dataframe(
    filtered_df[[
        "market_cap_rank", "name", "symbol",
        "price_change_percentage_1h_in_currency",
        "price_change_percentage_24h_in_currency",
        "formatted_price",
        "formatted_market_cap",
        "market_cap_change_percentage_24h"
    ]].rename(columns={
        "market_cap_rank": "Rank",
        "name": "Name",
        "symbol": "Symbol",
        "price_change_percentage_1h_in_currency": "1h Change (%)",
        "price_change_percentage_24h_in_currency": "24h Change (%)",
        "formatted_price": "Current Price (INR)",
        "formatted_market_cap": "Market Cap (INR)",
        "market_cap_change_percentage_24h": "MCap Change 24h (%)"
    }),
    use_container_width=True,
    height=900
)
