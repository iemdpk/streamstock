import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from pymongo import MongoClient
import certifi
from datetime import datetime
import pytz

# --- MongoDB Load ---
@st.cache_data(ttl=300)
def load_mongo_data():
    client = MongoClient("mongodb+srv://iemdpk:Imback2play@localserver.cwqbg.mongodb.net/?retryWrites=true&w=majority", tlsCAFile=certifi.where())
    db = client["crypto"]
    collection = db["snapshots"]
    return pd.DataFrame(list(collection.find({}, {"id": 1, "price_change_percentage_1h_in_currency": 1, "_id": 0,"timestamp":1})))

# --- INR Formatting ---
def format_inr(value):
    try:
        num = float(value)
        if num < 1e5:
            return f"{num:,.2f}"
        int_part, dec_part = str(f"{num:.2f}").split(".")
        last3 = int_part[-3:]
        rest = int_part[:-3]
        if rest:
            rest = ",".join([rest[max(i - 2, 0):i] for i in range(len(rest), 0, -2)][::-1])
            formatted = rest + "," + last3
        else:
            formatted = last3
        return f"₹ {formatted}.{dec_part}"
    except:
        return "₹ 0.00"

def get_length_before_decimal(value):
    try:
        return len(str(int(float(value))))
    except:
        return 0

def format_pct(val):
    try:
        return round(float(val), 2)
    except:
        return 0.0

# --- Buy/Sell/Hold logic ---
def get_indicator(row):
    try:
        mongo = float(row.get("mongo_1h_change", 0))
        api = float(row.get("price_change_percentage_1h_in_currency", 0))
        day = float(row.get("price_change_percentage_24h_in_currency", 0))

        if mongo > 0.2 and api > 0.2 and day > 0:
            return "BUY"
        elif mongo < -0.5 and api < -0.5 and day < 0:
            return "SELL"
        else:
            return "HOLD"
    except:
        return "HOLD"

# --- CoinGecko Load ---
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
    if response.status_code == 200:
        return pd.DataFrame(response.json())
    return pd.DataFrame()

# --- Load Data ---
df = load_data()
mongo_df = load_mongo_data()

st.set_page_config(page_title="Crypto Dashboard", layout="wide")
st.title("🪙 Crypto Dashboard")

if df.empty or mongo_df.empty:
    st.error("❌ Failed to load data from CoinGecko or MongoDB")
    st.stop()

# --- Merge Mongo data ---
mongo_df.rename(columns={"price_change_percentage_1h_in_currency": "mongo_1h_change"}, inplace=True)
df = df.merge(mongo_df, on="id", how="left")

# --- Market Sentiment (API vs MongoDB 1h) ---
api_avg = df["price_change_percentage_1h_in_currency"].mean()
mongo_avg = df["mongo_1h_change"].mean()
sentiment = "📈 Market is Bullish" if api_avg > mongo_avg else "📉 Market is Bearish"

st.markdown(f"""
### 🧠 Market Sentiment (1h %)
- API Avg: `{api_avg:.2f}%`
- DB Avg: `{mongo_avg:.2f}%`
- **{sentiment}**
""")
raw_ts = mongo_df["timestamp"].iloc[0]  # or .max() if needed

# Convert to datetime object with proper timezone
try:
    # If it's already a datetime object (not string), this will still work
    dt = pd.to_datetime(raw_ts).tz_convert("Asia/Kolkata")
except:
    dt = pd.to_datetime(raw_ts).tz_localize("UTC").tz_convert("Asia/Kolkata")

# Format to 'Month Day, Year – HH:MM:SS AM/PM IST'
formatted_ts = dt.strftime("%B %-d, %Y – %I:%M:%S %p IST")

# Show in Streamlit
st.markdown(f"🕒 **Last API Update:** `{formatted_ts}`")

# --- Sidebar Filters ---
st.sidebar.header("🔍 Filters")
max_rank = int(df["market_cap_rank"].dropna().max())
rank_input = st.sidebar.number_input("Market Cap Rank ≤", 1, max_rank, min(200, max_rank))
filtered_df = df[df["market_cap_rank"] <= rank_input].copy()

price_min = st.sidebar.text_input("Price ≥ (INR)", "")
if price_min.strip():
    try:
        filtered_df = filtered_df[filtered_df["current_price"] >= float(price_min.replace(",", ""))]
    except:
        st.sidebar.error("❌ Invalid min price")

price_max = st.sidebar.text_input("Price ≤ (INR)", "")
if price_max.strip():
    try:
        filtered_df = filtered_df[filtered_df["current_price"] <= float(price_max.replace(",", ""))]
    except:
        st.sidebar.error("❌ Invalid max price")

# --- Comparison Filter: 1h % (API) vs 1h % (DB) ---

compare_option = st.sidebar.selectbox(
    "Compare live prices:",
    ("All", "API % > DB %", "API % < DB %")
)

if compare_option == "API % > DB %":
    filtered_df = filtered_df[filtered_df["price_change_percentage_1h_in_currency"] > filtered_df["mongo_1h_change"]]
elif compare_option == "API % < DB %":
    filtered_df = filtered_df[filtered_df["price_change_percentage_1h_in_currency"] < filtered_df["mongo_1h_change"]]


# --- % Change Filters ---
def apply_pct_filter(df, column, label):
    if column not in df.columns:
        return df
    opt = st.sidebar.selectbox(f"{label} Price Change (%)", ["All", "Positive", "Negative"], key=column)
    if opt == "Positive":
        return df[df[column] > 0]
    elif opt == "Negative":
        return df[df[column] < 0]
    return df

filtered_df = apply_pct_filter(filtered_df, "price_change_percentage_1h_in_currency", "1h")
filtered_df = apply_pct_filter(filtered_df, "price_change_percentage_24h_in_currency", "24h")
filtered_df = apply_pct_filter(filtered_df, "price_change_percentage_7d_in_currency", "7d")
filtered_df = apply_pct_filter(filtered_df, "price_change_percentage_14d_in_currency", "14d")
filtered_df = apply_pct_filter(filtered_df, "price_change_percentage_30d_in_currency", "30d")
filtered_df = apply_pct_filter(filtered_df, "market_cap_change_percentage_24h", "MCap 24h")

# --- Format and Indicator ---
filtered_df["formatted_price"] = filtered_df["current_price"].apply(format_inr)
filtered_df["formatted_market_cap"] = filtered_df["market_cap"].apply(format_inr)
filtered_df["market_cap_length"] = filtered_df["market_cap"].apply(get_length_before_decimal)
filtered_df["Indicator"] = filtered_df.apply(get_indicator, axis=1)

# Format %
for col in ["price_change_percentage_1h_in_currency", "mongo_1h_change", "price_change_percentage_24h_in_currency"]:
    filtered_df[col] = filtered_df[col].apply(format_pct)

# --- 24h Sentiment ---
positive_count = (filtered_df["price_change_percentage_24h_in_currency"] > 0).sum()
negative_count = (filtered_df["price_change_percentage_24h_in_currency"] < 0).sum()
day_sentiment = "📈 Bullish" if positive_count > negative_count else "📉 Bearish"
st.markdown(f"### 📊 24h Sentiment: {day_sentiment}")
st.write(f"✅ Positive: {positive_count} | ❌ Negative: {negative_count}")

# --- Data Table ---
st.subheader(f"📋 {len(filtered_df)} Coins")
st.dataframe(
    filtered_df[[
        "market_cap_rank", "name", "symbol",
        "price_change_percentage_1h_in_currency", "mongo_1h_change",
        "price_change_percentage_24h_in_currency",
        "price_change_percentage_7d_in_currency",
        "price_change_percentage_14d_in_currency",
        "price_change_percentage_30d_in_currency",
        "Indicator",
        "formatted_price", "formatted_market_cap"
    ]].rename(columns={
        "market_cap_rank": "Rank",
        "name": "Name",
        "symbol": "Symbol",
        "price_change_percentage_1h_in_currency": "1h % (API)",
        "mongo_1h_change": "1h % (DB)",
        "price_change_percentage_24h_in_currency": "24h (%)",
        "price_change_percentage_7d_in_currency": "7d (%)",
        "price_change_percentage_14d_in_currency": "14d (%)",
        "price_change_percentage_30d_in_currency": "30d (%)",
        "formatted_price": "Price (₹)",
        "formatted_market_cap": "Market Cap (₹)",
        "Indicator": "Buy/Sell/Hold"
    }),
    use_container_width=True,
    height=1000
)

# --- Top Movers ---
st.subheader("📊 Top Movers")
timeframe_options = {
    "1h": "price_change_percentage_1h_in_currency",
    "24h": "price_change_percentage_24h_in_currency",
    "7d": "price_change_percentage_7d_in_currency",
    "14d": "price_change_percentage_14d_in_currency",
    "30d": "price_change_percentage_30d_in_currency",
}
time_choice = st.selectbox("Choose Timeframe", list(timeframe_options.keys()))
time_col = timeframe_options[time_choice]

if time_col in filtered_df.columns:
    top_gainers = filtered_df[filtered_df[time_col] > 0].sort_values(time_col, ascending=False).head(10)
    top_losers = filtered_df[filtered_df[time_col] < 0].sort_values(time_col).head(10)

    st.markdown(f"### 📈 Top Gainers ({time_choice})")
    fig_gain = px.bar(top_gainers, x="name", y=time_col, text=time_col)
    fig_gain.update_traces(texttemplate="%{text:.2f}%", textposition="outside")
    fig_gain.update_layout(xaxis_tickangle=-45, height=400)
    st.plotly_chart(fig_gain, use_container_width=True)

    st.markdown(f"### 📉 Top Losers ({time_choice})")
    fig_loss = px.bar(top_losers, x="name", y=time_col, text=time_col)
    fig_loss.update_traces(texttemplate="%{text:.2f}%", textposition="outside")
    fig_loss.update_layout(xaxis_tickangle=-45, height=400)
    st.plotly_chart(fig_loss, use_container_width=True)
