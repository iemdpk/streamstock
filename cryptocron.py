import requests
import pandas as pd
from pymongo import MongoClient
import certifi
from datetime import datetime
import pytz

def fetch_and_store():

    symbols_to_match = """
    ETH,BTC,SOL,XRP,FARTCOIN,ENA,DOGE,PEPE,LINK,SUI,ADA,LTC,UNI,ARB,PENGU,AVAX,TRUMP,CYBER,BONK,AAVE,WIF,OP,CRV,SEI,XLM,APT,TON,ETC,NEAR,WLD,ETHFI,SHIB,ONDO,BNB,HBAR,TIA,FIL,PENDLE,INJ,HIFI,LDO,TAO,SKL,EIGEN,BCH,BOME,JUP,VIRTUAL,MYRO,PNUT,BIO,AERO,CFX,PEOPLE,FLOKI,THE,MAGIC,DOT,MOODENG,SPX,ATOM,ALGO,ANIME,MKR,ORDI,ZRO,GALA,POPCAT,OM,RENDER,IP,JTO,IO,S,VINE,SAND,TRX,MLN,ALT,ENS,AI16Z,CAKE,TRB,POL,ZK,COMP,XMR,JASMY,KMNO,AIXBT,SHELL,VET,MEME,NOT,ICP,STX,STRK,PAXG,GOAT,KAS,PYTH,BRETT,SSV,AVAAI,000MOG,ILV,DYDX,APE,GRIFFAIN,NEIROETH,SWARMS,MASK,EGLD,KAITO,BB,PROM,ACH,COOKIE,OMNI,CAT,LISTA,XTZ,RSR,SOLV,ARC,MEW,KAIA,GRASS,LQTY,PIPPIN,HFT,DOGS,CKB,RPL,XAI,PARTI,EPIC,RVN,ID,MELANIA,W,ZIL,BANANA,AI,SUSHI,CETUS,AR,MORPHO,ZEC,IMX,GRT,BAN,AXL,MAVIA,ZRX,FLM,HIPPO,ARPA,ARKM,PORTAL,VANRY,KSM,ORCA,RUNE,PHB,NIL,RARE,GMX,ME,HMSTR,DASH,QNT,GMT,UMA,IOST,USUAL,ONT,AUCTION,HOT,BMT,FXS,USTC,MOVR,MANA,COW,BSW,1INCH,SWELL,T,VELODROME,GPS,OGN,SPELL,FIDA,THETA,PLUME,TRU,SUN,CHILLGUY,SCR,DRIFT,VANA,SONIC,AXS,REZ,RATS,DEXE,NEO,DENT,UXLINK,ROSE,ATH,RLC,ICX,HOOK,PONKE,FLOW,XCN,TOKEN,STG,CHESS,DEGEN,BLUR,CELO,ACX,TWT,G,IOTA,FIO,LEVER,ALPHA,JOE,PERP,MANTA,HEI,BNT,ASTR,OXT,ATA,C98,BIGTIME,POLYX,PHA,ONE,ETHW,LRC,EDU,WAXP,BSV,B3,MOCA,SUPER,ZEREBRO,CELR,VVV,LPT,GAS,HIVE,ALCH,YFI,MUBARAK,AEVO,MINA,VTHO,COTI,KAVA,WOO,CATI,RED,SNX,X,COS,ONG,AGLD,ZETA,STEEM,KDA,IOTX,ZEN,LUNC,SAFE,ENJ,KOMA,DYM,QUICK,YGG,SAGA,ARK,SLERF,GLM,NTRN,USDC,NFP,SYS,LUNA2,ACT,ALICE,QTUM,METIS,FORTH,LUMIA,AKT,VIC,BICO,API3,SYN,CGPT,CTSI,RDNT,STORJ,PIXEL,VOXEL,BAKE,TNSR,SCRT,TLM,SXP,POWR,HIGH,CHR,BEL,RONIN,XVS,AVA,SFP,NKN,NMR,FLUX,RIF
    """.replace("\n","").split(",")

    # Container for all fetched coins
    all_coins = []

    for page in range(1, 10):
        url = "https://api.coingecko.com/api/v3/coins/markets"
        print("this is running ",page);
        params = {
            "vs_currency": "inr",
            "order": "volume_desc",
            "per_page": 250,
            "page":page,
            "sparkline": "false",
            "locale": "en",
            "precision": 2,
            "price_change_percentage": "1h,24h,7d,14d,30d,200d,1y"
        }
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            all_coins.extend(data)
    
    data = response.json()
    matched_coins = [coin for coin in all_coins if coin['symbol'].upper() in symbols_to_match]

    df = pd.DataFrame(matched_coins)

    # Convert to Indian Standard Time (IST) and format as string
    ist = pytz.timezone("Asia/Kolkata")
    india_time = datetime.now(ist)
    df["timestamp"] = india_time.strftime("%Y-%m-%d %H:%M:%S %Z%z")

    # Connect to MongoDB
    client = MongoClient(
        "mongodb+srv://iemdpk:Imback2play@localserver.cwqbg.mongodb.net/?retryWrites=true&w=majority",
        tlsCAFile=certifi.where()
    )
    db = client["crypto"]
    collection = db["snapshots"]

    # Clean old data
    collection.delete_many({})

    # Save data
    collection.insert_many(df.to_dict(orient="records"))
    print("✅ Data saved to MongoDB at", df["timestamp"].iloc[0])

if __name__ == "__main__":
    fetch_and_store()
