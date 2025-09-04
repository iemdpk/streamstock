import requests
import pandas as pd
from datetime import datetime
from pymongo import MongoClient
from twilio.rest import Client
import certifi
from telegram import Bot
import pytz
import numpy as np

# --- Config ---
MONGO_URI = "mongodb+srv://iemdpk:Imback2play@localserver.cwqbg.mongodb.net/"
DB_NAME = "crypto_alerts"
COLLECTION_NAME = "status"
collection_old = "snapshots"

BOT_TOKEN = "8391929163:AAEmfYxxh9L1hpsWvIuaMNEC3cZBNdjXcG4"   # From BotFather
CHAT_ID = "1334996232" 
TIMEZONE = "Asia/Kolkata" 

TWILIO_SID = "ACee2bb220157dd2b516ea651340976347"
TWILIO_AUTH = "049075ad3046f09c5927700c75ed16c2"
TWILIO_FROM = "+12232239309"  # Twilio number
TWILIO_TO = "+918709476349"  # Your number

def send_telegram_alert(message):
    bot = Bot(token=BOT_TOKEN)
    india_tz = pytz.timezone(TIMEZONE)
    indian_time = datetime.now(india_tz).strftime("%d-%m-%Y %H:%M IST")
    final_msg = f"{message}\n\n⌛ Update: {indian_time}"
    bot.send_message(chat_id=CHAT_ID, text=final_msg, parse_mode="Markdown")

def fetch_crypto_data():
    """Fetch top cryptocurrencies from CoinGecko, multiple pages, and match specific symbols"""
    
    symbols_to_match = """
        ETC,BTC,SOL,XRP,ENA,SUI,ADA,PEPE,DOGE,AVAX,BONK,WIF,
        ARB,LTC,SHIB,OP,TIA,BNB,INJ,ETHFI,ONDO,APT,TON,DOT,
        GALA,FLOKI,LDO,BCH,ORDI,APE,AEVO
    """.replace("\n", "").split(",")

    all_coins = []

    # Fetch multiple pages (1–12)
    for page in range(1, 12):
        url = "https://api.coingecko.com/api/v3/coins/markets"
        params = {
            "vs_currency": "inr",
            "order": "volume_desc",
            "per_page": 250,
            "page": page,
            "sparkline": False,
            "locale": "en",
            "precision": 2,
            "price_change_percentage": "1h,24h,7d,14d,30d,200d,1y"
        }
        print(f"Fetching page {page}...")
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            all_coins.extend(data)
        else:
            print(f"Failed to fetch page {page}: {response.status_code}")

    # Filter coins that match symbols
    matched_coins = [coin for coin in all_coins if coin['symbol'].upper() in symbols_to_match]

    # Add rank
    for i, coin in enumerate(matched_coins):
        coin['rank'] = i + 1

    df = pd.DataFrame(matched_coins)

    client = MongoClient("mongodb+srv://iemdpk:Imback2play@localserver.cwqbg.mongodb.net/?retryWrites=true&w=majority", tlsCAFile=certifi.where())
    db = client["crypto"]
    collection = db["snapshots"]
    previous_data = list(db["tracker"].find({}))

    return df, previous_data

def call_twilio(message):
    """Make a Twilio voice call with the given message"""
    try:
        client = Client(TWILIO_SID, TWILIO_AUTH)
        call = client.calls.create(
            twiml=f'<Response><Say>{message}</Say></Response>',
            from_=TWILIO_FROM,
            to=TWILIO_TO
        )
        print(f"Twilio call initiated: {call.sid}")
        return True
    except Exception as e:
        print(f"Failed to make Twilio call: {e}")
        return False

def calculate_average_change(df, cols):
    """Calculate average change across specified columns for each coin"""
    df_copy = df.copy()
    # Replace NaN values with 0 for calculation
    for col in cols:
        df_copy[col] = df_copy[col].fillna(0)
    
    # Calculate average change for each coin
    df_copy['avg_change'] = df_copy[cols].mean(axis=1)
    return df_copy

def get_top_coins(df, cols, sentiment):
    """Get top 5 bullish or bearish coins based on average change"""
    df_with_avg = calculate_average_change(df, cols)
    
    if sentiment == "📈 Bullish":
        # Get top 5 coins with highest positive average change
        top_coins = df_with_avg.nlargest(5, 'avg_change')
        coin_type = "📈 Bullish"
    else:
        # Get top 5 coins with lowest (most negative) average change
        top_coins = df_with_avg.nsmallest(5, 'avg_change')
        coin_type = "📉 Bearish"
    
    coin_list = []
    for idx, coin in top_coins.iterrows():
        symbol = coin['symbol'].upper()
        name = coin['name']
        avg_change = coin['avg_change']
        current_price = coin['current_price']
        
        # Format the change with appropriate emoji
        if avg_change > 0:
            change_str = f"+{avg_change:.2f}%"
            emoji = "🟢"
        else:
            change_str = f"{avg_change:.2f}%"
            emoji = "🔴"
        
        coin_list.append({
            'symbol': symbol,
            'name': name,
            'avg_change': avg_change,
            'change_str': change_str,
            'current_price': current_price,
            'emoji': emoji
        })
    
    return coin_list, coin_type

def format_top_coins_message(coin_list, coin_type):
    """Format the top coins message for Telegram"""
    message_lines = [f"\n🏆 **Top 5 {coin_type.replace('📈 ', '').replace('📉 ', '')} Coins:**"]
    
    for i, coin in enumerate(coin_list, 1):
        line = f"{i}. {coin['emoji']} **{coin['symbol']}** ({coin['name'][:15]}{'...' if len(coin['name']) > 15 else ''})"
        line += f"\n   💰 ₹{coin['current_price']:,.2f} | {coin['change_str']}"
        message_lines.append(line)
    
    return "\n".join(message_lines)

def main():
    df, previous_data = fetch_crypto_data()

    db0 = pd.DataFrame(previous_data[0]["coins"])
    db1 = pd.DataFrame(previous_data[1]["coins"])
    db2 = pd.DataFrame(previous_data[2]["coins"])
    db3 = pd.DataFrame(previous_data[3]["coins"])
    db4 = pd.DataFrame(previous_data[4]["coins"])

    db0.rename(columns={"price_change_percentage_1h_in_currency": "mongo_10_change"}, inplace=True)
    db1.rename(columns={"price_change_percentage_1h_in_currency": "mongo_20_change"}, inplace=True)
    db2.rename(columns={"price_change_percentage_1h_in_currency": "mongo_30_change"}, inplace=True)
    db3.rename(columns={"price_change_percentage_1h_in_currency": "mongo_40_change"}, inplace=True)
    db4.rename(columns={"price_change_percentage_1h_in_currency": "mongo_50_change"}, inplace=True)

    df = df.merge(db0[["id", "mongo_10_change"]], on="id", how="left")
    df = df.merge(db1[["id", "mongo_20_change"]], on="id", how="left")
    df = df.merge(db2[["id", "mongo_30_change"]], on="id", how="left")
    df = df.merge(db3[["id", "mongo_40_change"]], on="id", how="left")
    df = df.merge(db4[["id", "mongo_50_change"]], on="id", how="left")

    cols = ["mongo_10_change", "mongo_20_change", "mongo_30_change", "mongo_40_change", "mongo_50_change"]
    
    # Determine overall sentiment
    total_positive = sum((df[col] > 0).sum() for col in cols)
    total_negative = sum((df[col] < 0).sum() for col in cols)

    current_sentiment = "📈 Bullish" if total_positive > total_negative else "📉 Bearish"

    # Get top 5 coins based on current sentiment
    top_coins, coin_type = get_top_coins(df, cols, current_sentiment)
    top_coins_message = format_top_coins_message(top_coins, coin_type)

    # MongoDB connection
    client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]

    # Check existing document
    prev = collection.find_one({"type": "top100_1h"})

    if prev is None:
        # Insert if nothing exists
        collection.insert_one({
            "type": "top100_1h",
            "status": current_sentiment,
            "total_negative": str(total_negative),
            "total_positive": str(total_positive),
            "updated_at": datetime.utcnow()
        })
        
        # Send alerts for first time setup
        telegram_msg = f"🆕 **Initial Sentiment Setup**\n\nSentiment: {current_sentiment}\nPositive: {total_positive}\nNegative: {total_negative}{top_coins_message}"
        send_telegram_alert(telegram_msg)
        
        # Create top coins summary for voice call
        top_coins_voice = ", ".join([f"{coin['symbol']} at {coin['change_str']}" for coin in top_coins[:3]])
        call_message = f"Crypto sentiment tracker initialized. Current sentiment is {current_sentiment.replace('📈 ', '').replace('📉 ', '')}. Positive count: {total_positive}, Negative count: {total_negative}. Top coins are {top_coins_voice}."
        call_twilio(call_message)
        print("Inserted new sentiment data and sent alerts.")
        
    else:
        # Compare old vs new sentiment
        prev_sentiment = prev.get("status", "")
        prev_pos = int(prev.get("total_positive", "0"))
        prev_neg = int(prev.get("total_negative", "0"))

        # Check if sentiment changed
        sentiment_changed = prev_sentiment != current_sentiment
        
        changes = []
        if prev_pos != total_positive:
            changes.append(f"Positive: {prev_pos} → {total_positive}")
        if prev_neg != total_negative:
            changes.append(f"Negative: {prev_neg} → {total_negative}")

        if sentiment_changed:
            # Update MongoDB with new sentiment
            collection.update_one(
                {"_id": prev["_id"]},
                {"$set": {
                    "status": current_sentiment,
                    "total_negative": str(total_negative),
                    "total_positive": str(total_positive),
                    "updated_at": datetime.utcnow()
                }}
            )
            
            # Prepare alert messages
            change_details = " | ".join(changes) if changes else "Same counts"
            telegram_msg = f"🚨 **SENTIMENT CHANGE ALERT**\n\n🔄 {prev_sentiment} → {current_sentiment}\n\n📊 **Details:**\n{change_details}{top_coins_message}"
            
            # Send Telegram alert
            send_telegram_alert(telegram_msg)
            
            # Create top coins summary for voice call
            top_coins_voice = ", ".join([f"{coin['symbol']} at {coin['change_str']}" for coin in top_coins[:3]])
            call_message = f"Crypto Alert! Sentiment changed from {prev_sentiment.replace('📈 ', '').replace('📉 ', '')} to {current_sentiment.replace('📈 ', '').replace('📉 ', '')}. {change_details.replace(' → ', ' changed from ').replace(':', ' ')}. Top performing coins are {top_coins_voice}."
            call_success = call_twilio(call_message)
            
            print(f"🚨 SENTIMENT CHANGED: {prev_sentiment} → {current_sentiment}")
            print(f"Telegram alert sent. Twilio call {'successful' if call_success else 'failed'}.")
            
        elif changes:
            # Numbers changed but sentiment stayed the same
            print(int(prev_pos) - total_positive, int(prev_neg) - total_negative)
            
            collection.update_one(
                {"_id": prev["_id"]},
                {"$set": {
                    "total_negative": str(total_negative),
                    "total_positive": str(total_positive),
                    "updated_at": datetime.utcnow()
                }}
            )
            
            # Calculate net positive and negative changes
            positive_net_change = total_positive - prev_pos
            negative_net_change = total_negative - prev_neg
            
            # Check for significant positive change (>15 increase in positive sentiment)
            if positive_net_change >= 15:
                telegram_msg = f"📈 **SIGNIFICANT POSITIVE CHANGE**\n\n🔥 Positive sentiment increased by {positive_net_change}\n\nCurrent: {current_sentiment}\n📊 Details: {' | '.join(changes)}\n\n⚠️ **Alert:** Large positive movement! Sentiment may shift to more **Bullish**!{top_coins_message}"
                
                top_coins_voice = ", ".join([f"{coin['symbol']} at {coin['change_str']}" for coin in top_coins[:3]])
                call_message = f"Crypto Alert! Significant positive change detected. Positive sentiment increased by {positive_net_change}. Current sentiment is {current_sentiment.replace('📈 ', '').replace('📉 ', '')} but may shift to more Bullish due to large positive movement. Top coins are {top_coins_voice}."
                
                print(f"📈 SIGNIFICANT POSITIVE CHANGE: +{positive_net_change} - May shift to Bullish")
                
            # Check for significant negative change (>15 increase in negative sentiment)  
            elif negative_net_change >= 15:
                telegram_msg = f"📉 **SIGNIFICANT NEGATIVE CHANGE**\n\n🔻 Negative sentiment increased by {negative_net_change}\n\nCurrent: {current_sentiment}\n📊 Details: {' | '.join(changes)}\n\n⚠️ **Alert:** Large negative movement! Sentiment may shift to more **Bearish**!{top_coins_message}"
                
                top_coins_voice = ", ".join([f"{coin['symbol']} at {coin['change_str']}" for coin in top_coins[:3]])
                call_message = f"Crypto Alert! Significant negative change detected. Negative sentiment increased by {negative_net_change}. Current sentiment is {current_sentiment.replace('📈 ', '').replace('📉 ', '')} but may shift to more Bearish due to large negative movement. Top coins are {top_coins_voice}."
                
                print(f"📉 SIGNIFICANT NEGATIVE CHANGE: +{negative_net_change} - May shift to Bearish")
                
            # Check for significant decrease in positive sentiment (could indicate shift to bearish)
            elif positive_net_change <= -15:
                telegram_msg = f"📉 **POSITIVE SENTIMENT DROPPING**\n\n🔻 Positive sentiment decreased by {abs(positive_net_change)}\n\nCurrent: {current_sentiment}\n📊 Details: {' | '.join(changes)}\n\n⚠️ **Alert:** Sharp positive drop! Sentiment may shift to **Bearish**!{top_coins_message}"
                
                top_coins_voice = ", ".join([f"{coin['symbol']} at {coin['change_str']}" for coin in top_coins[:3]])
                call_message = f"Crypto Alert! Significant drop in positive sentiment detected. Positive sentiment decreased by {abs(positive_net_change)}. Current sentiment is {current_sentiment.replace('📈 ', '').replace('📉 ', '')} but may shift to Bearish due to positive sentiment dropping. Top coins are {top_coins_voice}."
                
                print(f"📉 POSITIVE SENTIMENT DROPPING: -{abs(positive_net_change)} - May shift to Bearish")
                
            # Check for significant decrease in negative sentiment (could indicate shift to bullish)
            elif negative_net_change <= -15:
                telegram_msg = f"📈 **NEGATIVE SENTIMENT DROPPING**\n\n🔥 Negative sentiment decreased by {abs(negative_net_change)}\n\nCurrent: {current_sentiment}\n📊 Details: {' | '.join(changes)}\n\n⚠️ **Alert:** Sharp negative drop! Sentiment may shift to **Bullish**!{top_coins_message}"
                
                top_coins_voice = ", ".join([f"{coin['symbol']} at {coin['change_str']}" for coin in top_coins[:3]])
                call_message = f"Crypto Alert! Significant drop in negative sentiment detected. Negative sentiment decreased by {abs(negative_net_change)}. Current sentiment is {current_sentiment.replace('📈 ', '').replace('📉 ', '')} but may shift to Bullish due to negative sentiment dropping. Top coins are {top_coins_voice}."
                
                print(f"📈 NEGATIVE SENTIMENT DROPPING: -{abs(negative_net_change)} - May shift to Bullish")
                
            else:
                # Regular update - no significant change
                telegram_msg = f"📊 **Numbers Updated** (Same Sentiment)\n\nSentiment: {current_sentiment}\nPositive change: {positive_net_change:+d}\nNegative change: {negative_net_change:+d}\n\n📊 Details: {' | '.join(changes)}{top_coins_message}"
                send_telegram_alert(telegram_msg)
                print(f"Numbers changed but sentiment remained the same. Pos: {positive_net_change:+d}, Neg: {negative_net_change:+d}")
                return  # Skip sending alert again
            
            send_telegram_alert(telegram_msg)
            
        else:
            # No change at all
            telegram_msg = f"✅ **No Change**\n\nSentiment: {current_sentiment}\nPositive: {total_positive} | Negative: {total_negative}{top_coins_message}"
            send_telegram_alert(telegram_msg)
            print("No change in sentiment or numbers.")

    client.close()

if __name__ == "__main__":
    main()
