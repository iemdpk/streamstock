import streamlit as st
import pandas as pd
import requests

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

# 2️⃣ Current Price (INR) Range
min_price = float(df["current_price"].min())
max_price = float(df["current_price"].max())
price_range = st.sidebar.slider(
    "2️⃣ Current Price Range (INR)", 
    min_value=min_price, 
    max_value=max_price, 
    value=(min_price, max_price)
)

# --- Apply rank + price filter first ---
filtered_df = df[
    (df["market_cap_rank"] <= rank_input) &
    (df["current_price"] >= price_range[0]) &
    (df["current_price"] <= price_range[1])
]

# 3️⃣ Price Change 1h %
change_1h = st.sidebar.selectbox("3️⃣ 1h Price % Change", ["All", "Positive", "Negative"])
if change_1h == "Positive":
    filtered_df = filtered_df[filtered_df["price_change_percentage_1h_in_currency"] > 0]
elif change_1h == "Negative":
    filtered_df = filtered_df[filtered_df["price_change_percentage_1h_in_currency"] < 0]

# 4️⃣ Price Change 24h %
change_24h = st.sidebar.selectbox("4️⃣ 24h Price % Change", ["All", "Positive", "Negative"])
if change_24h == "Positive":
    filtered_df = filtered_df[filtered_df["price_change_percentage_24h"] > 0]
elif change_24h == "Negative":
    filtered_df = filtered_df[filtered_df["price_change_percentage_24h"] < 0]

# 5️⃣ Market Cap Change 24h %
mcap_change_24h = st.sidebar.selectbox("5️⃣ Market Cap % Change (24h)", ["All", "Positive", "Negative"])
if mcap_change_24h == "Positive":
    filtered_df = filtered_df[filtered_df["market_cap_change_percentage_24h"] > 0]
elif mcap_change_24h == "Negative":
    filtered_df = filtered_df[filtered_df["market_cap_change_percentage_24h"] < 0]

# --- Show Data ---
st.subheader(f"📊 Showing {len(filtered_df)} coins")
st.dataframe(
    filtered_df[[
        "market_cap_rank","name", "symbol", "current_price","price_change_percentage_1h_in_currency",
        "price_change_percentage_24h",
        "market_cap",
        "market_cap_change_percentage_24h"
    ]].sort_values(by="market_cap_rank").reset_index(drop=True),
    use_container_width=True
)
