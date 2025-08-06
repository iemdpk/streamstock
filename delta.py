import requests
import pandas as pd
from datetime import datetime, timedelta, timezone

BASE = "https://api.india.delta.exchange/v2"

def get_perpetual_symbols():
    url = f"{BASE}/products"
    r = requests.get(url)
    r.raise_for_status()
    products = r.json().get("result", [])
    return [
        p["symbol"] for p in products
        if p.get("contract_type") == "perpetual_futures" and p.get("state") == "live"
    ]

def fetch_candles(symbol, resolution, start_ts, end_ts):
    url = f"{BASE}/history/candles"
    params = {
        "symbol": symbol,
        "resolution": resolution,
        "start": int(start_ts),
        "end": int(end_ts)
    }
    r = requests.get(url, params=params)
    if r.status_code != 200:
        print(f"[{symbol} | {resolution}] HTTP {r.status_code}")
        return pd.DataFrame()
    data = r.json().get("result", [])
    if not data:
        print(f"[{symbol} | {resolution}] No data")
        return pd.DataFrame()
    df = pd.DataFrame(data)
    df["symbol"] = symbol
    df["resolution"] = resolution
    df["time"] = pd.to_datetime(df["time"], unit="s", utc=True).dt.tz_convert("Asia/Kolkata")
    return df

def main():
    print("🔍 Fetching live perpetual futures...")
    symbols = get_perpetual_symbols()
    print(f"✅ Found {len(symbols)} perpetual futures symbols.")

    now = datetime.now(timezone.utc)
    
    # 🔁 Add or remove resolutions as needed
    durations = {
        "1m": 1,
        "5m": 5,
        "15m": 15,
        "1h": 60,
        "4h": 240,
        "1d": 1440
    }

    all_data = []

    for symbol in symbols[:5]:  # You can increase/remove limit
        for resolution, minutes in durations.items():
            start = (now - timedelta(minutes=minutes * 10)).timestamp()  # 10 candles back
            end = now.timestamp()
            print(f"📥 Fetching {resolution} candles for: {symbol}")
            df = fetch_candles(symbol, resolution, start, end)
            if not df.empty:
                all_data.append(df)

    if all_data:
        final_df = pd.concat(all_data, ignore_index=True)
        print("✅ Sample of fetched candles:")
        print(final_df.head())

        # Optional: Save to CSV
        final_df.to_csv("delta_futures_candles.csv", index=False)
        print("💾 Saved to delta_futures_candles.csv")
    else:
        print("❌ No candles fetched.")

if __name__ == "__main__":
    main()
