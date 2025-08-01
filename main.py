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
        "price_change_percentage": "1h"
    }
    response = requests.get(url, params=params)
    return pd.DataFrame(response.json())

df = load_data()

# --- Title ---
st.set_page_config(page_title="Crypto Filter", layout="wide")
st.title("🪙 Crypto Dashboard - CoinGecko INR")

# --- Sidebar Filters ---
st.sidebar.header("🔍 Multi-Level Filters")

# 1️⃣ Market Cap Rank ≤
max_rank = int(df["market_cap_rank"].dropna().max())
rank_input = st.sidebar.number_input(
    "1️⃣ Market Cap Rank ≤", 
    min_value=1, max_value=max_rank, value=max_rank
)

# --- Initial filter only by rank ---
filtered_df = df[df["market_cap_rank"] <= rank_input]

# 2️⃣ Current Price ≥ (Min)
price_min_input = st.sidebar.text_input("2️⃣ Current Price ≥ (INR)", "")
if price_min_input.strip():
    try:
        min_val = float(price_min_input.replace(",", ""))
        filtered_df = filtered_df[filtered_df["current_price"] >= min_val]
    except ValueError:
        st.sidebar.error("❌ Enter a valid number for min price")

# 3️⃣ Current Price ≤ (Max)
price_max_input = st.sidebar.text_input("3️⃣ Current Price ≤ (INR)", "")
if price_max_input.strip():
    try:
        max_val = float(price_max_input.replace(",", ""))
        filtered_df = filtered_df[filtered_df["current_price"] <= max_val]
    except ValueError:
        st.sidebar.error("❌ Enter a valid number for max price")

# 4️⃣ Price Change 1h %
change_1h = st.sidebar.selectbox("4️⃣ 1h Price % Change", ["All", "Positive", "Negative"])
if change_1h == "Positive":
    filtered_df = filtered_df[filtered_df["price_change_percentage_1h_in_currency"] > 0]
elif change_1h == "Negative":
    filtered_df = filtered_df[filtered_df["price_change_percentage_1h_in_currency"] < 0]

# 5️⃣ Price Change 24h %
change_24h = st.sidebar.selectbox("5️⃣ 24h Price % Change", ["All", "Positive", "Negative"])
if change_24h == "Positive":
    filtered_df = filtered_df[filtered_df["price_change_percentage_24h"] > 0]
elif change_24h == "Negative":
    filtered_df = filtered_df[filtered_df["price_change_percentage_24h"] < 0]

# 6️⃣ Market Cap Change 24h %
mcap_change_24h = st.sidebar.selectbox("6️⃣ Market Cap % Change (24h)", ["All", "Positive", "Negative"])
if mcap_change_24h == "Positive":
    filtered_df = filtered_df[filtered_df["market_cap_change_percentage_24h"] > 0]
elif mcap_change_24h == "Negative":
    filtered_df = filtered_df[filtered_df["market_cap_change_percentage_24h"] < 0]

# --- Format numbers ---
filtered_df["formatted_price"] = filtered_df["current_price"].apply(format_inr)
filtered_df["formatted_market_cap"] = filtered_df["market_cap"].apply(format_inr)

# --- Show Data ---
st.subheader(f"📊 Showing {len(filtered_df)} coins")
st.dataframe(
    filtered_df[[
        "market_cap_rank", "symbol", 
        "price_change_percentage_1h_in_currency",
        "price_change_percentage_24h",
        "formatted_price",
        "formatted_market_cap",
        "market_cap_change_percentage_24h"
    ]].rename(columns={
        "market_cap_rank": "Rank",
        "symbol": "Symbol",
        "formatted_price": "Current Price (INR)",
        "price_change_percentage_1h_in_currency": "1h Change (%)",
        "price_change_percentage_24h": "24h Change (%)",
        "formatted_market_cap": "Market Cap (INR)",
        "market_cap_change_percentage_24h": "MCap Change 24h (%)"
    }),
    use_container_width=True
)
