import streamlit as st
import pandas as pd
import pymongo
import certifi
from datetime import datetime

# --- MongoDB Configuration ---
MONGO_URI = "mongodb+srv://iemdpk:Imback2play@localserver.cwqbg.mongodb.net/deltaexchange"
TIMEZONE = "Asia/Kolkata"

# --- MongoDB Connection ---
@st.cache_resource
def get_mongo_collection():
    try:
        client = pymongo.MongoClient(MONGO_URI, tlsCAFile=certifi.where())
        db = client.get_database()
        return db.futures_data
    except Exception as e:
        st.error(f"❌ MongoDB connection failed: {e}")
        return None

# --- Fetch Data from MongoDB ---
@st.cache_data(ttl=60)
def fetch_data_from_mongo():
    collection = get_mongo_collection()
    if collection is None:
        return pd.DataFrame(), None
    try:
        data = list(collection.find())
        if not data:
            return pd.DataFrame(), None
        df = pd.DataFrame(data)
        df.drop(columns=["_id"], inplace=True, errors="ignore")

        if "timestamp" in df.columns and not pd.api.types.is_datetime64_any_dtype(df["timestamp"]):
            df["timestamp"] = pd.to_datetime(df["timestamp"])

        latest_time = df["timestamp"].max() if "timestamp" in df.columns else None
        return df, latest_time
    except Exception as e:
        st.error(f"❌ Error fetching data from MongoDB: {e}")
        return pd.DataFrame(), None

# --- Compute Reverse-Based Percent Changes ---
def compute_reverse_percent_changes(df):
    cols = [
        "symbol", "1m_close", "5m_close", "15m_close", "1h_close", "4h_close", "1d_close"
    ]
    df = df[cols].copy()

    # Calculate reverse % changes: shorter vs longer
    df["1m %"] = ((df["1m_close"] - df["5m_close"]) / df["5m_close"]) * 100
    df["5m %"] = ((df["5m_close"] - df["15m_close"]) / df["15m_close"]) * 100
    df["15m %"] = ((df["15m_close"] - df["1h_close"]) / df["1h_close"]) * 100
    df["1h %"] = ((df["1h_close"] - df["4h_close"]) / df["4h_close"]) * 100
    df["4h %"] = ((df["4h_close"] - df["1d_close"]) / df["1d_close"]) * 100

    # Final column order
    final_cols = [
        "symbol",
        "1m_close", "5m_close", "15m_close", "1h_close", "4h_close", "1d_close",
        "1m %", "5m %", "15m %", "1h %", "4h %"
    ]
    return df[final_cols]

# --- Streamlit App ---
def main():
    st.set_page_config(page_title="Delta Futures Dashboard", layout="wide")
    st.title("📊 Delta Futures Prices & Reverse % Change")

    # Fetch from MongoDB
    with st.spinner("📦 Fetching data from MongoDB..."):
        close_prices, last_updated = fetch_data_from_mongo()

    # Show last update
    if last_updated:
        st.success(f"✅ Data last updated at: `{last_updated}`")

    if not close_prices.empty:
        df_result = compute_reverse_percent_changes(close_prices)

        st.dataframe(
            df_result.style.format({
                "1m_close": "{:.4f}", "5m_close": "{:.4f}",
                "15m_close": "{:.4f}", "1h_close": "{:.4f}",
                "4h_close": "{:.4f}", "1d_close": "{:.4f}",
                "1m %": "{:.2f}%", "5m %": "{:.2f}%", "15m %": "{:.2f}%",
                "1h %": "{:.2f}%", "4h %": "{:.2f}%"
            }),
            use_container_width=True,
            height=800
        )

        # Download button
        csv = df_result.to_csv(index=False).encode("utf-8")
        st.download_button(
            "📥 Download as CSV",
            data=csv,
            file_name="delta_futures_all_closes.csv",
            mime="text/csv"
        )
    else:
        st.warning("⚠️ No data available in MongoDB.")

if __name__ == "__main__":
    main()
