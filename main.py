import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from pymongo import MongoClient
import certifi
from datetime import datetime
import pytz
import matplotlib.pyplot as plt

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

# --- Calculate Target and Stop Loss ---
def calculate_target_stop(row):
    try:
        current_price = float(row['current_price'])
        # 5% target, 3% stop loss (adjustable)
        target = current_price * 1.05
        stop_loss = current_price * 0.97
        target_pct = 5.0  # Default target percentage
        stop_loss_pct = 3.0  # Default stop loss percentage
        return target, stop_loss, target_pct, stop_loss_pct
    except:
        return 0, 0, 0, 0

# --- CoinGecko Load ---
@st.cache_data(ttl=300)
def load_data():
    symbols_to_match = """
ETH,BTC,SOL,XRP,FARTCOIN,ENA,DOGE,PEPE,LINK,SUI,ADA,LTC,UNI,ARB,PENGU,AVAX,TRUMP,CYBER,BONK,AAVE,WIF,OP,CRV,SEI,XLM,APT,TON,ETC,NEAR,WLD,ETHFI,SHIB,ONDO,BNB,HBAR,TIA,FIL,PENDLE,INJ,HIFI,LDO,TAO,SKL,EIGEN,BCH,BOME,JUP,VIRTUAL,MYRO,PNUT,BIO,AERO,CFX,PEOPLE,FLOKI,THE,MAGIC,DOT,MOODENG,SPX,ATOM,ALGO,ANIME,MKR,ORDI,ZRO,GALA,POPCAT,OM,RENDER,IP,JTO,IO,S,VINE,SAND,TRX,MLN,ALT,ENS,AI16Z,CAKE,TRB,POL,ZK,COMP,XMR,JASMY,KMNO,AIXBT,SHELL,VET,MEME,NOT,ICP,STX,STRK,PAXG,GOAT,KAS,PYTH,BRETT,SSV,AVAAI,000MOG,ILV,DYDX,APE,GRIFFAIN,NEIROETH,SWARMS,MASK,EGLD,KAITO,BB,PROM,ACH,COOKIE,OMNI,CAT,LISTA,XTZ,RSR,SOLV,ARC,MEW,KAIA,GRASS,LQTY,PIPPIN,HFT,DOGS,CKB,RPL,XAI,PARTI,EPIC,RVN,ID,MELANIA,W,ZIL,BANANA,AI,SUSHI,CETUS,AR,MORPHO,ZEC,IMX,GRT,BAN,AXL,MAVIA,ZRX,FLM,HIPPO,ARPA,ARKM,PORTAL,VANRY,KSM,ORCA,RUNE,PHB,NIL,RARE,GMX,ME,HMSTR,DASH,QNT,GMT,UMA,IOST,USUAL,ONT,AUCTION,HOT,BMT,FXS,USTC,MOVR,MANA,COW,BSW,1INCH,SWELL,T,VELODROME,GPS,OGN,SPELL,FIDA,THETA,PLUME,TRU,SUN,CHILLGUY,SCR,DRIFT,VANA,SONIC,AXS,REZ,RATS,DEXE,NEO,DENT,UXLINK,ROSE,ATH,RLC,ICX,HOOK,PONKE,FLOW,XCN,TOKEN,STG,CHESS,DEGEN,BLUR,CELO,ACX,TWT,G,IOTA,FIO,LEVER,ALPHA,JOE,PERP,MANTA,HEI,BNT,ASTR,OXT,ATA,C98,BIGTIME,POLYX,PHA,ONE,ETHW,LRC,EDU,WAXP,BSV,B3,MOCA,SUPER,ZEREBRO,CELR,VVV,LPT,GAS,HIVE,ALCH,YFI,MUBARAK,AEVO,MINA,VTHO,COTI,KAVA,WOO,CATI,RED,SNX,X,COS,ONG,AGLD,ZETA,STEEM,KDA,IOTX,ZEN,LUNC,SAFE,ENJ,KOMA,DYM,QUICK,YGG,SAGA,ARK,SLERF,GLM,NTRN,USDC,NFP,SYS,LUNA2,ACT,ALICE,QTUM,METIS,FORTH,LUMIA,AKT,VIC,BICO,API3,SYN,CGPT,CTSI,RDNT,STORJ,PIXEL,VOXEL,BAKE,TNSR,SCRT,TLM,SXP,POWR,HIGH,CHR,BEL,RONIN,XVS,AVA,SFP,NKN,NMR,FLUX,RIF
""".replace("\n","").split(",")
    
    all_coins = []

    # Fetch multiple pages
    for page in range(1, 11):
        url = "https://api.coingecko.com/api/v3/coins/markets"
        params = {
            "vs_currency": "inr",
            "order": "market_cap_desc",
            "per_page": 250,
            "page": page,
            "sparkline": False,
            "locale": "en",
            "precision": 2,
            "price_change_percentage": "1h,24h,7d,14d,30d,200d,1y"
        }
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            all_coins.extend(data)
        else:
            print(f"Failed to fetch page {page}: {response.status_code}")

    # Filter by symbol list
    matched_coins = [coin for coin in all_coins if coin['symbol'].upper() in symbols_to_match]

    # Convert to DataFrame
    df = pd.DataFrame(matched_coins)
    return df

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
    dt = pd.to_datetime(raw_ts).tz_convert("Asia/Kolkata")
except:
    dt = pd.to_datetime(raw_ts).tz_localize("UTC").tz_convert("Asia/Kolkata")

# Format timestamp
formatted_ts = dt.strftime("%B %-d, %Y – %I:%M:%S %p IST")

# Show in Streamlit
st.markdown(f"🕒 **Last API Update:** `{formatted_ts}`")

# --- Sidebar Filters ---
st.sidebar.header("🔍 Filters")

# Advanced Filters Section
st.sidebar.subheader("Advanced Filters")

# Volatility Filter
volatility_option = st.sidebar.selectbox(
    "Volatility Level",
    ["All", "Low (<1%)", "Medium (1-5%)", "High (>5%)"]
)

# Volume Filter
volume_option = st.sidebar.selectbox(
    "24h Volume",
    ["All", "Low (<₹100Cr)", "Medium (₹100-500Cr)", "High (>₹500Cr)"]
)

# Market Cap Filter
mcap_option = st.sidebar.selectbox(
    "Market Cap Size",
    ["All", "Small (<₹1,000Cr)", "Mid (₹1,000-10,000Cr)", "Large (>₹10,000Cr)"]
)

# Basic Filters Section
st.sidebar.subheader("Basic Filters")
max_rank = int(df["market_cap_rank"].dropna().max())
rank_input = st.sidebar.number_input("Market Cap Rank ≤", 1, max_rank, min(max_rank, max_rank))
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



st.sidebar.subheader("24h min max")
price_min24 = st.sidebar.text_input("24h min %", "")
if price_min24.strip():
    try:
        min_val = float(price_min24.replace(",", ""))
        filtered_df = filtered_df[filtered_df["price_change_percentage_24h"] >= min_val]
    except ValueError:
        st.sidebar.error("❌ Invalid min % (24h)")

price_max24 = st.sidebar.text_input("24h max %", "")
if price_max24.strip():
    try:
        max_val = float(price_max24.replace(",", ""))
        filtered_df = filtered_df[filtered_df["price_change_percentage_24h"] <= max_val]
    except ValueError:
        st.sidebar.error("❌ Invalid max % (24h)")

st.sidebar.subheader("1h min max")
price_min1 = st.sidebar.text_input("1h min %", "")
if price_min1.strip():
    try:
        min_val = float(price_min1.replace(",", ""))
        filtered_df = filtered_df[filtered_df["price_change_percentage_1h_in_currency"] >= min_val]
    except ValueError:
        st.sidebar.error("❌ Invalid min % (1h)")

price_max1 = st.sidebar.text_input("1h max %", "")
if price_max1.strip():
    try:
        max_val = float(price_max1.replace(",", ""))
        filtered_df = filtered_df[filtered_df["price_change_percentage_1h_in_currency"] <= max_val]
    except ValueError:
        st.sidebar.error("❌ Invalid max % (1h)")



# Apply Advanced Filters
if volatility_option == "Low (<1%)":
    filtered_df = filtered_df[filtered_df["price_change_percentage_24h"].abs() < 1]
elif volatility_option == "Medium (1-5%)":
    filtered_df = filtered_df[(filtered_df["price_change_percentage_24h"].abs() >= 1) & 
                            (filtered_df["price_change_percentage_24h"].abs() <= 5)]
elif volatility_option == "High (>5%)":
    filtered_df = filtered_df[filtered_df["price_change_percentage_24h"].abs() > 5]

if volume_option == "Low (<₹100Cr)":
    filtered_df = filtered_df[filtered_df["total_volume"] < 10000000000]
elif volume_option == "Medium (₹100-500Cr)":
    filtered_df = filtered_df[(filtered_df["total_volume"] >= 10000000000) & 
                            (filtered_df["total_volume"] <= 50000000000)]
elif volume_option == "High (>₹500Cr)":
    filtered_df = filtered_df[filtered_df["total_volume"] > 50000000000]

if mcap_option == "Small (<₹1,000Cr)":
    filtered_df = filtered_df[filtered_df["market_cap"] < 100000000000]
elif mcap_option == "Mid (₹1,000-10,000Cr)":
    filtered_df = filtered_df[(filtered_df["market_cap"] >= 100000000000) & 
                            (filtered_df["market_cap"] <= 1000000000000)]
elif mcap_option == "Large (>₹10,000Cr)":
    filtered_df = filtered_df[filtered_df["market_cap"] > 1000000000000]

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
filtered_df = apply_pct_filter(filtered_df, "mongo_1h_change", "1h mongo")
filtered_df = apply_pct_filter(filtered_df, "price_change_percentage_24h_in_currency", "24h")
filtered_df = apply_pct_filter(filtered_df, "price_change_percentage_7d_in_currency", "7d")
filtered_df = apply_pct_filter(filtered_df, "price_change_percentage_14d_in_currency", "14d")
filtered_df = apply_pct_filter(filtered_df, "price_change_percentage_30d_in_currency", "30d")
filtered_df = apply_pct_filter(filtered_df, "market_cap_change_percentage_24h", "MCap 24h")

# --- Calculate Target and Stop Loss ---
filtered_df[['target_price', 'stop_loss', 'target_pct', 'stop_loss_pct']] = filtered_df.apply(
    calculate_target_stop, axis=1, result_type='expand'
)

# --- Format and Indicator ---
filtered_df["formatted_price"] = filtered_df["current_price"].apply(format_inr)
filtered_df["formatted_market_cap"] = filtered_df["market_cap"].apply(format_inr)
filtered_df["formatted_target"] = filtered_df["target_price"].apply(format_inr)
filtered_df["formatted_stop_loss"] = filtered_df["stop_loss"].apply(format_inr)
filtered_df["market_cap_length"] = filtered_df["market_cap"].apply(get_length_before_decimal)
filtered_df["Indicator"] = filtered_df.apply(get_indicator, axis=1)

# Format percentages for display
filtered_df["target_pct"] = filtered_df["target_pct"].apply(lambda x: f"{x:.1f}%")
filtered_df["stop_loss_pct"] = filtered_df["stop_loss_pct"].apply(lambda x: f"{x:.1f}%")

# Format %
for col in ["price_change_percentage_1h_in_currency", "mongo_1h_change", "price_change_percentage_24h_in_currency"]:
    filtered_df[col] = filtered_df[col].apply(format_pct)

# --- 24h Sentiment ---
positive_count = (filtered_df["price_change_percentage_24h_in_currency"] > 0).sum()
negative_count = (filtered_df["price_change_percentage_24h_in_currency"] < 0).sum()
day_sentiment = "📈 Bullish" if positive_count > negative_count else "📉 Bearish"
st.markdown(f"### 📊 24h Sentiment: {day_sentiment}")
st.write(f"✅ Positive: {positive_count} | ❌ Negative: {negative_count}")

# 1h sentiment one hour
positive_count_1h = (filtered_df["price_change_percentage_1h_in_currency"] > 0).sum()
negative_count_1h = (filtered_df["price_change_percentage_1h_in_currency"] < 0).sum()

hour_sentiment = "📈 Bullish" if positive_count_1h > negative_count_1h else "📉 Bearish"

st.markdown(f"### ⏳ 1h Sentiment: {hour_sentiment}")
st.write(f"✅ Positive: {positive_count_1h} | ❌ Negative: {negative_count_1h}")


# --- Data Table ---
st.subheader(f"📋 {len(filtered_df)} Coins")

# Sort by market cap rank by default
filtered_df = filtered_df.sort_values("market_cap_rank")

# Display the table with pinned market cap rank

def format_pct1(val):
    try:
        # Remove % sign if present and convert to float
        if isinstance(val, str):
            val = val.replace('%', '')
        return round(float(val), 2)
    except:
        return 0.00

# Then update the styling code:
def color_negative_red(val):
    try:
        # Handle both numeric and string-with-% values
        num = float(str(val).replace('%','')) if isinstance(val, str) else float(val)
        color = 'green' if num > 0 else 'red' if num < 0 else 'black'
        return f'color: {color}'
    except:
        return 'color: black'

# Create display dataframe with numeric values
display_df = filtered_df[[
    "market_cap_rank", "name", "symbol",
    "price_change_percentage_1h_in_currency", "mongo_1h_change",
    "price_change_percentage_24h_in_currency",
    "price_change_percentage_7d_in_currency",
    "price_change_percentage_14d_in_currency",
    "price_change_percentage_30d_in_currency",
    "Indicator",
    "formatted_price", 
    "target_pct",
    "formatted_target",
    "stop_loss_pct",
    "formatted_stop_loss",
    "formatted_market_cap"
]].copy()

# Convert percentage columns to numeric
for col in [
    "price_change_percentage_1h_in_currency", "mongo_1h_change",
    "price_change_percentage_24h_in_currency",
    "price_change_percentage_7d_in_currency",
    "price_change_percentage_14d_in_currency",
    "price_change_percentage_30d_in_currency",
    "target_pct", "stop_loss_pct"
]:
    display_df[col] = display_df[col].apply(format_pct1)
# Example: Add a new column 'Diff (API-DB)' = API 1h % - DB 1h %
display_df["Diff (API-DB)"] = (
    display_df["price_change_percentage_1h_in_currency"] 
    - display_df["mongo_1h_change"]
)

# Rename columns
display_df = display_df.rename(columns={
    "market_cap_rank": "Rank",
    "name": "Name",
    "symbol": "Symbol",
    "price_change_percentage_1h_in_currency": "1h % (API)",
    "mongo_1h_change": "1h % (DB)",
    "Diff (API-DB)": "Diff 1h %",
    "price_change_percentage_24h_in_currency": "24h (%)",
    "price_change_percentage_7d_in_currency": "7d (%)",
    "price_change_percentage_14d_in_currency": "14d (%)",
    "price_change_percentage_30d_in_currency": "30d (%)",
    "formatted_price": "Price (₹)",
    "target_pct": "Target %",
    "formatted_target": "Target (₹)",
    "stop_loss_pct": "Stop Loss %",
    "formatted_stop_loss": "Stop Loss (₹)",
    "formatted_market_cap": "Market Cap (₹)",
    "Indicator": "Action"
})

# Apply styling
styled_df = display_df.style.applymap(color_negative_red, subset=[
    "1h % (API)", "1h % (DB)", "Diff 1h %", "24h (%)", "7d (%)", 
    "14d (%)", "30d (%)", "Target %", "Stop Loss %"
]).format({
    "1h % (API)": "{:.2f}%",
    "1h % (DB)": "{:.2f}%",
    "Diff 1h %": "{:.2f}%",
    "24h (%)": "{:.2f}%",
    "7d (%)": "{:.2f}%",
    "14d (%)": "{:.2f}%",
    "30d (%)": "{:.2f}%",
    "Target %": "{:.1f}%",
    "Stop Loss %": "{:.1f}%"
})

# Display in Streamlit
st.dataframe(
    styled_df,
    use_container_width=True,
    height=1000,
    column_config={
        "Rank": st.column_config.NumberColumn(
            "Rank",
            help="Market Cap Rank",
            width="small",
        )
    },
    column_order=(
        "Rank", "Name", "Symbol", "1h % (API)", "1h % (DB)", "Diff 1h %",
        "24h (%)", "7d (%)", "14d (%)", "30d (%)", "Action",
        "Price (₹)", "Target %", "Target (₹)", "Stop Loss %", 
        "Stop Loss (₹)", "Market Cap (₹)"
    )
)



# ===== CONFIG =====
MONGO_URI = "mongodb+srv://iemdpk:Imback2play@localserver.cwqbg.mongodb.net/?retryWrites=true&w=majority"
DB_NAME = "crypto_t"

@st.cache_resource(ttl=300)
def get_data():
    client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
    db = client[DB_NAME]

    def fetch_collection(name):
        return list(db[name].find({}))

    return fetch_collection("positive"), fetch_collection("negative")

def analyze_collection(data, trend_label):
    results = []
    for doc in data:
        history = doc.get("price_history", [])
        if len(history) < 2:
            continue

        first = history[0]
        last = history[-1]

        prices = [point["price"] for point in history]
        percents_24h = [point.get("percentage24h", 0) for point in history]

        first_price = first["price"]
        last_price = last["price"]
        delta_price = round(last_price - first_price, 4)

        first_24h = first.get("percentage24h", 0)
        last_24h = last.get("percentage24h", 0)
        percent_change = round(last_24h - first_24h, 2)

        first_1h = first.get("percentage1h", 0)
        last_1h = last.get("percentage1h", 0)
        delta_1h = round(last_1h - first_1h, 4)

        if percent_change > 0:
            status = "🔼 UP"
        elif percent_change < 0:
            status = "🔻 DOWN"
        else:
            status = "⏸️ No Change"

        results.append({
            "Symbol": doc["symbol"].upper(),
            "Trend": trend_label,
            "Status": status,
            "Marketcap": doc.get("marketcap", None),   # ✅ NEW
            "First Price": first_price,
            "Last Price": last_price,
            "Δ Price": delta_price,
            "% Change": percent_change,
            "First 24h %": first_24h,
            "Last 24h %": last_24h,
            "First 1h %": first_1h,
            "Last 1h %": last_1h,
            "Δ 1h %": delta_1h,
            "Chart Data (24h %)": percents_24h,
            "Last Updated": last["timestamp"]
        })
    return pd.DataFrame(results)

def generate_line_chart(values, symbol):
    fig, ax = plt.subplots(figsize=(5, 1.5))
    ax.plot(values, marker='o', linewidth=1.5)
    ax.set_title(f"{symbol} 24h % Change", fontsize=10)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.grid(True, alpha=0.3)
    st.pyplot(fig)

def highlight_pos_neg(val):
    if isinstance(val, (int, float)):
        if val > 0:
            return ' color: green; font-weight: bold;'
        elif val < 0:
            return ' color: red; font-weight: bold;'
    return ''

def format_2f(val):
    if isinstance(val, float):
        return f"{val:.2f}"
    return val

# ===== Streamlit UI =====
st.set_page_config("📊 Crypto Trend Analyzer", layout="wide")
st.title("📊 Mover Gainer")
st.caption("Auto-refreshes every 20 minutes")

# Load Data
positive_data, negative_data = get_data()
positive_df = analyze_collection(positive_data, "Gainer")
negative_df = analyze_collection(negative_data, "Loser")

# Reordered columns: Symbol first, then % Change, then 1h %, then others
cols = [
    "Symbol",
    "Marketcap",   # ✅ added
    "% Change",
    "Δ Price",
    "Δ 1h %",
    "First 24h %",
    "Last 24h %",
    "First 1h %",
    "Last 1h %",
    "Status",
    "First Price",
    "Last Price",
    "Last Updated"
]


# ===== Show Positive Gainers =====
st.subheader("🚀 Positive / Gainers")
if not positive_df.empty:
    st.dataframe(
        positive_df[cols]
        .style.applymap(highlight_pos_neg, subset=[
            "% Change",
            "First 1h %", "Last 1h %", "Δ 1h %",
            "Δ Price",
            "First 24h %", "Last 24h %"
        ])
        .format(format_2f),
        use_container_width=True
    )
else:
    st.write("No positive/gainer data available.")

# ===== Show Negative Losers =====
st.subheader("📉 Negative / Losers")
if not negative_df.empty:
    st.dataframe(
        negative_df[cols]
        .style.applymap(highlight_pos_neg, subset=[
            "% Change",
            "First 1h %", "Last 1h %", "Δ 1h %",
            "Δ Price",
            "First 24h %", "Last 24h %"
        ])
        .format(format_2f),
        use_container_width=True
    )
else:
    st.write("No negative/loser data available.")

# ===== Mini Charts Section =====
st.markdown("### 📈 Mini Trend Charts (24h % Movement)")

# Show charts for positive coins
st.markdown("#### 🚀 Positive / Gainers Charts")
for idx, row in positive_df.iterrows():
    with st.expander(f"{row['Symbol']}"):
        generate_line_chart(row["Chart Data (24h %)"], row["Symbol"])

# Show charts for negative coins
st.markdown("#### 📉 Negative / Losers Charts")
for idx, row in negative_df.iterrows():
    with st.expander(f"{row['Symbol']}"):
        generate_line_chart(row["Chart Data (24h %)"], row["Symbol"])
