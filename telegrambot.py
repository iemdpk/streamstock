import requests
import pandas as pd
from telegram import Bot
from datetime import datetime
import pytz

# --- Configuration ---
BOT_TOKEN = "7542846023:AAEvykrFTN1gs50aJsSgSxyik185v27Lfkc"   # From BotFather
CHAT_ID = "1334996232"       # From getUpdates or @userinfobot
TIMEZONE = "Asia/Kolkata"

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
    """Return sentiment text based on bullish percentage"""
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
    """Return sentiment stats for given DataFrame"""
    df = df.dropna(subset=['price_change_percentage_1h_in_currency', 'price_change_percentage_24h_in_currency'])

    # --- 1h stats ---
    rising_1h = (df['price_change_percentage_1h_in_currency'] > 0).sum()
    bullish_percent_1h = (rising_1h / len(df)) * 100

    # --- 24h stats ---
    rising_24h = (df['price_change_percentage_24h_in_currency'] > 0).sum()
    bullish_percent_24h = (rising_24h / len(df)) * 100

    return {
        'coins': len(df),
        '1h': bullish_percent_1h,
        '1h_sentiment': get_sentiment(bullish_percent_1h),
        '24h': bullish_percent_24h,
        '24h_sentiment': get_sentiment(bullish_percent_24h)
    }

def generate_report(overall, top100, bitcoin_data):
    """Generate final Hinglish report"""
    report = ""

    # 1h
    report += f"⏳ *1h({overall['coins']} coins)*: {overall['1h_sentiment']} ({overall['1h']:.1f}% coins upar)\n"
    report += f"⏳ *1h(100)*: {top100['1h_sentiment']} ({top100['1h']:.1f}% coins upar)\n\n"

    # 24h
    report += f"🕓 *24h({overall['coins']} coins)*: {overall['24h_sentiment']} ({overall['24h']:.1f}% coins upar)\n"
    report += f"🕓 *24h(100)*: {top100['24h_sentiment']} ({top100['24h']:.1f}% coins upar)\n\n"

    # BTC
    # report += f"₿ *Bitcoin*: 1h {bitcoin_data['1h']:+.2f}%, 24h {bitcoin_data['24h']:+.2f}% (Rank #{bitcoin_data['rank']})"

    return report

def send_telegram_alert(message):
    bot = Bot(token=BOT_TOKEN)
    india_tz = pytz.timezone(TIMEZONE)
    indian_time = datetime.now(india_tz).strftime("%d-%m-%Y %H:%M IST")
    final_msg = f"{message}\n\n⌛ Update: {indian_time}"
    bot.send_message(chat_id=CHAT_ID, text=final_msg, parse_mode="Markdown")

def main():
    df = fetch_crypto_data()

    # Analysis
    overall_stats = analyze_market(df)
    top100_stats = analyze_market(df.head(100))

    # Bitcoin data
    btc = df[df['name'] == 'Bitcoin']
    bitcoin_data = {
        '1h': btc['price_change_percentage_1h_in_currency'].values[0],
        '24h': btc['price_change_percentage_24h_in_currency'].values[0],
        'rank': btc['rank'].values[0]
    }

    # Report
    report = generate_report(overall_stats, top100_stats, bitcoin_data)
    send_telegram_alert(report)

if __name__ == "__main__":
    main()
