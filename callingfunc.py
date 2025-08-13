import requests
import pandas as pd
from datetime import datetime
from pymongo import MongoClient
from twilio.rest import Client
import certifi


# --- Config ---
MONGO_URI = "mongodb+srv://iemdpk:Imback2play@localserver.cwqbg.mongodb.net/"
DB_NAME = "crypto_alerts"
COLLECTION_NAME = "status"

TWILIO_SID = "ACee2bb220157dd2b516ea651340976347"
TWILIO_AUTH = "049075ad3046f09c5927700c75ed16c2"
TWILIO_FROM = "+12232239309"  # Twilio number
TWILIO_TO = "+918709476349"  # Your number


def fetch_crypto_data():
    """Fetch top cryptocurrencies from CoinGecko, multiple pages, and match specific symbols"""
    
    symbols_to_match = """
    ETH,BTC,SOL,XRP,FARTCOIN,ENA,DOGE,PEPE,LINK,SUI,ADA,LTC,UNI,ARB,PENGU,AVAX,TRUMP,CYBER,BONK,AAVE,WIF,OP,CRV,SEI,XLM,APT,TON,ETC,NEAR,WLD,ETHFI,SHIB,ONDO,BNB,HBAR,TIA,FIL,PENDLE,INJ,HIFI,LDO,TAO,SKL,EIGEN,BCH,BOME,JUP,VIRTUAL,MYRO,PNUT,BIO,AERO,CFX,PEOPLE,FLOKI,THE,MAGIC,DOT,MOODENG,SPX,ATOM,ALGO,ANIME,MKR,ORDI,ZRO,GALA,POPCAT,OM,RENDER,IP,JTO,IO,S,VINE,SAND,TRX,MLN,ALT,ENS,AI16Z,CAKE,TRB,POL,ZK,COMP,XMR,JASMY,KMNO,AIXBT,SHELL,VET,MEME,NOT,ICP,STX,STRK,PAXG,GOAT,KAS,PYTH,BRETT,SSV,AVAAI,000MOG,ILV,DYDX,APE,GRIFFAIN,NEIROETH,SWARMS,MASK,EGLD,KAITO,BB,PROM,ACH,COOKIE,OMNI,CAT,LISTA,XTZ,RSR,SOLV,ARC,MEW,KAIA,GRASS,LQTY,PIPPIN,HFT,DOGS,CKB,RPL,XAI,PARTI,EPIC,RVN,ID,MELANIA,W,ZIL,BANANA,AI,SUSHI,CETUS,AR,MORPHO,ZEC,IMX,GRT,BAN,AXL,MAVIA,ZRX,FLM,HIPPO,ARPA,ARKM,PORTAL,VANRY,KSM,ORCA,RUNE,PHB,NIL,RARE,GMX,ME,HMSTR,DASH,QNT,GMT,UMA,IOST,USUAL,ONT,AUCTION,HOT,BMT,FXS,USTC,MOVR,MANA,COW,BSW,1INCH,SWELL,T,VELODROME,GPS,OGN,SPELL,FIDA,THETA,PLUME,TRU,SUN,CHILLGUY,SCR,DRIFT,VANA,SONIC,AXS,REZ,RATS,DEXE,NEO,DENT,UXLINK,ROSE,ATH,RLC,ICX,HOOK,PONKE,FLOW,XCN,TOKEN,STG,CHESS,DEGEN,BLUR,CELO,ACX,TWT,G,IOTA,FIO,LEVER,ALPHA,JOE,PERP,MANTA,HEI,BNT,ASTR,OXT,ATA,C98,BIGTIME,POLYX,PHA,ONE,ETHW,LRC,EDU,WAXP,BSV,B3,MOCA,SUPER,ZEREBRO,CELR,VVV,LPT,GAS,HIVE,ALCH,YFI,MUBARAK,AEVO,MINA,VTHO,COTI,KAVA,WOO,CATI,RED,SNX,X,COS,ONG,AGLD,ZETA,STEEM,KDA,IOTX,ZEN,LUNC,SAFE,ENJ,KOMA,DYM,QUICK,YGG,SAGA,ARK,SLERF,GLM,NTRN,USDC,NFP,SYS,LUNA2,ACT,ALICE,QTUM,METIS,FORTH,LUMIA,AKT,VIC,BICO,API3,SYN,CGPT,CTSI,RDNT,STORJ,PIXEL,VOXEL,BAKE,TNSR,SCRT,TLM,SXP,POWR,HIGH,CHR,BEL,RONIN,XVS,AVA,SFP,NKN,NMR,FLUX,RIF
    """.replace("\n", "").split(",")

    all_coins = []

    # Fetch multiple pages (1–10)
    for page in range(1, 11):
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
    return df



def get_sentiment(bullish_percent):
    if bullish_percent >= 60:
        return "Strong Bullish ✅"
    elif bullish_percent >= 55:
        return "Moderate Bullish 📈"
    elif bullish_percent >= 45:
        return "Neutral ⚖️"
    elif bullish_percent >= 40:
        return "Moderate Bearish 📉"
    else:
        return "Strong Bearish ❌"

def analyze_market(df):
    df = df.dropna(subset=['price_change_percentage_1h_in_currency'])
    rising_1h = (df['price_change_percentage_1h_in_currency'] > 0).sum()
    bullish_percent_1h = (rising_1h / len(df)) * 100
    return {
        'coins': len(df),
        '1h': bullish_percent_1h,
        '1h_sentiment': get_sentiment(bullish_percent_1h)
    }

def call_twilio(message):
    client = Client(TWILIO_SID, TWILIO_AUTH)
    client.calls.create(
        twiml=f'<Response><Say>{message}</Say></Response>',
        from_=TWILIO_FROM,
        to=TWILIO_TO
    )

def main():
    df = fetch_crypto_data()
    top100_stats = analyze_market(df.head(100))
    current_status = top100_stats['1h_sentiment']

    # MongoDB
    client = MongoClient(MONGO_URI,tlsCAFile=certifi.where())
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]

    prev = collection.find_one({"type": "top100_1h"})

    if not prev or prev.get("status") != current_status:
        # Status changed → call Twilio
        call_message = f"Crypto Alert! 1h Top100 status changed: {current_status}"
        call_twilio(call_message)

        # Update MongoDB
        collection.update_one(
            {"type": "top100_1h"},
            {"$set": {"status": current_status, "updated_at": datetime.utcnow()}},
            upsert=True
        )
        print(f"Status changed: {current_status} → Twilio call sent.")
    else:
        print(f"No change in status: {current_status} → No call.")

if __name__ == "__main__":
    main()
