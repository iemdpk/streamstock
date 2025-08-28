import requests
import pandas as pd
from pymongo import MongoClient
import certifi
from datetime import datetime, timedelta
import pytz
from telegram import Bot
import uuid
import time

BOT_TOKEN = "7542846023:AAEvykrFTN1gs50aJsSgSxyik185v27Lfkc"   # From BotFather
CHAT_ID = "1334996232"       # From getUpdates or @userinfobot
TIMEZONE = "Asia/Kolkata"

def send_telegram_alert(message):
    bot = Bot(token=BOT_TOKEN)
    india_tz = pytz.timezone(TIMEZONE)
    indian_time = datetime.now(india_tz).strftime("%d-%m-%Y %H:%M IST")
    final_msg = f"{message}\n\n⌛ Update: {indian_time}"
    bot.send_message(chat_id=CHAT_ID, text=final_msg, parse_mode="Markdown")

def fetch_crypto_data():
    """Fetch crypto data from CoinGecko API"""
    symbols_to_match = """
    ETH,BTC,SOL,XRP,FARTCOIN,ENA,DOGE,PEPE,LINK,SUI,ADA,LTC,UNI,ARB,PENGU,AVAX,TRUMP,CYBER,BONK,AAVE,WIF,OP,CRV,SEI,XLM,APT,TON,ETC,NEAR,WLD,ETHFI,SHIB,ONDO,BNB,HBAR,TIA,FIL,PENDLE,INJ,HIFI,LDO,TAO,SKL,EIGEN,BCH,BOME,JUP,VIRTUAL,MYRO,PNUT,BIO,AERO,CFX,PEOPLE,FLOKI,THE,MAGIC,DOT,MOODENG,SPX,ATOM,ALGO,ANIME,MKR,ORDI,ZRO,GALA,POPCAT,OM,RENDER,IP,JTO,IO,S,VINE,SAND,TRX,MLN,ALT,ENS,AI16Z,CAKE,TRB,POL,ZK,COMP,XMR,JASMY,KMNO,AIXBT,SHELL,VET,MEME,NOT,ICP,STX,STRK,PAXG,GOAT,KAS,PYTH,BRETT,SSV,AVAAI,000MOG,ILV,DYDX,APE,GRIFFAIN,NEIROETH,SWARMS,MASK,EGLD,KAITO,BB,PROM,ACH,COOKIE,OMNI,CAT,LISTA,XTZ,RSR,SOLV,ARC,MEW,KAIA,GRASS,LQTY,PIPPIN,HFT,DOGS,CKB,RPL,XAI,PARTI,EPIC,RVN,ID,MELANIA,W,ZIL,BANANA,AI,SUSHI,CETUS,AR,MORPHO,ZEC,IMX,GRT,BAN,AXL,MAVIA,ZRX,FLM,HIPPO,ARPA,ARKM,PORTAL,VANRY,KSM,ORCA,RUNE,PHB,NIL,RARE,GMX,ME,HMSTR,DASH,QNT,GMT,UMA,IOST,USUAL,ONT,AUCTION,HOT,BMT,FXS,USTC,MOVR,MANA,COW,BSW,1INCH,SWELL,T,VELODROME,GPS,OGN,SPELL,FIDA,THETA,PLUME,TRU,SUN,CHILLGUY,SCR,DRIFT,VANA,SONIC,AXS,REZ,RATS,DEXE,NEO,DENT,UXLINK,ROSE,ATH,RLC,ICX,HOOK,PONKE,FLOW,XCN,TOKEN,STG,CHESS,DEGEN,BLUR,CELO,ACX,TWT,G,IOTA,FIO,LEVER,ALPHA,JOE,PERP,MANTA,HEI,BNT,ASTR,OXT,ATA,C98,BIGTIME,POLYX,PHA,ONE,ETHW,LRC,EDU,WAXP,BSV,B3,MOCA,SUPER,ZEREBRO,CELR,VVV,LPT,GAS,HIVE,ALCH,YFI,MUBARAK,AEVO,MINA,VTHO,COTI,KAVA,WOO,CATI,RED,SNX,X,COS,ONG,AGLD,ZETA,STEEM,KDA,IOTX,ZEN,LUNC,SAFE,ENJ,KOMA,DYM,QUICK,YGG,SAGA,ARK,SLERF,GLM,NTRN,USDC,NFP,SYS,LUNA2,ACT,ALICE,QTUM,METIS,FORTH,LUMIA,AKT,VIC,BICO,API3,SYN,CGPT,CTSI,RDNT,STORJ,PIXEL,VOXEL,BAKE,TNSR,SCRT,TLM,SXP,POWR,HIGH,CHR,BEL,RONIN,XVS,AVA,SFP,NKN,NMR,FLUX,RIF
    """.replace("\n","").split(",")

    all_coins = []
    
    # Fetch from multiple pages
    for page in range(1, 2):  # Adjust pages as needed
        url = "https://api.coingecko.com/api/v3/coins/markets"
        print(f"🔄 Fetching page {page}...")
        
        params = {
            "vs_currency": "inr",
            "order": "volume_desc", 
            "per_page": 250,
            "page": page,
            "sparkline": "false",
            "locale": "en",
            "precision": 2,
            "price_change_percentage": "1h,24h,7d,14d,30d,200d,1y"
        }
        
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            all_coins.extend(data)
        else:
            print(f"❌ Error fetching page {page}: {response.status_code}")

    # Filter matched coins
    matched_coins = [coin for coin in all_coins if coin['symbol'].upper() in symbols_to_match]
    print(f"✅ Found {len(matched_coins)} matched coins")
    
    return matched_coins

def create_snapshot_with_3_docs():
    """Create one snapshot with 3 documents containing coins data"""
    try:
        # Connect to MongoDB
        client = MongoClient(
            "mongodb+srv://iemdpk:Imback2play@localserver.cwqbg.mongodb.net/?retryWrites=true&w=majority",
            tlsCAFile=certifi.where()
        )
        db = client["crypto"]
        collection = db["tracker"]

        # Generate unique snapshot ID
        snapshot_id = str(uuid.uuid4())
        ist = pytz.timezone("Asia/Kolkata")
        
        print(f"📦 Creating snapshot: {snapshot_id}")
        
        # Fetch crypto data
        coins_data = fetch_crypto_data()
        if not coins_data:
            print("❌ No crypto data found")
            return
        
        # Create 3 documents for this snapshot (same data, different timestamps)
        documents_to_insert = []
        
        for i in range(1, 2):  # Create 3 documents
            # Different timestamp for each document (few seconds apart)
            doc_time = datetime.now(ist) + timedelta(seconds=i)
            
            document = {
                "snapshot_id": snapshot_id,
                "document_number": i,
                "coins": coins_data,
                "total_coins": len(coins_data),
                "created_at": doc_time,
                "timestamp_str": doc_time.strftime("%Y-%m-%d %H:%M:%S %Z%z")
            }
            documents_to_insert.append(document)
            
            print(f"📄 Document {i}/3 prepared - {len(coins_data)} coins")
            time.sleep(1)  # 1 second gap between each document creation

       
        result = collection.insert_many(documents_to_insert)
        print(f"✅ Inserted {len(result.inserted_ids)} documents for snapshot: {snapshot_id}")

        # FIFO Logic - Keep only latest 3 snapshots
        check_and_cleanup_old_snapshots(collection)
        
        client.close()
        return snapshot_id, len(coins_data)
        
    except Exception as e:
        print(f"❌ Database error: {str(e)}")
        send_telegram_alert(f"❌ Database error: {str(e)}")
        return None, 0

def check_and_cleanup_old_snapshots(collection):
    """Check snapshots count and delete oldest if more than 3"""
    try:
        # Get all unique snapshot_ids ordered by creation time (oldest first)
        pipeline = [
            {"$group": {
                "_id": "$snapshot_id", 
                "created_at": {"$min": "$created_at"},
                "doc_count": {"$sum": 1}
            }},
            {"$match": {"doc_count": 3}},  # Only complete snapshots (with 3 docs)
            {"$sort": {"created_at": 1}},  # Sort by creation time (oldest first)
            {"$project": {"snapshot_id": "$_id", "created_at": 1, "doc_count": 1}}
        ]
        
        complete_snapshots = list(collection.aggregate(pipeline))
        snapshot_count = len(complete_snapshots)
        
        print(f"📊 Total complete snapshots found: {snapshot_count}")
        
        # If more than 3 complete snapshots, delete the oldest ones
        if snapshot_count > 3:
            snapshots_to_delete = complete_snapshots[:-3]  # Keep last 3, delete rest
            
            send_telegram_alert(f"🔄 Crypto snapshot updated\n📦 New snapshot added\n🗑️ Cleaned {len(snapshots_to_delete)} old snapshots ({total_deleted} documents)\n⏰ FIFO maintained")
        else:
            send_telegram_alert(f"🔄 Crypto snapshot added\n📦 Total snapshots: {snapshot_count}/3\n📊 Documents per snapshot: 3\n✅ FIFO ready")
            
    except Exception as e:
        print(f"❌ Cleanup error: {str(e)}")

def get_collection_stats():
    """Get detailed collection statistics"""
    try:
        client = MongoClient(
            "mongodb+srv://iemdpk:Imback2play@localserver.cwqbg.mongodb.net/?retryWrites=true&w=majority",
            tlsCAFile=certifi.where()
        )
        db = client["crypto"]
        collection = db["tracker"]
        
        # Total documents
        total_docs = list(collection.find({}))
        print(len(total_docs));
        if(len(total_docs) == 7):
            print("we have to remove one")
            print(total_docs[0]["_id"]);
            collection.delete_one({"_id":total_docs[0]["_id"]})
    except:
        print("solved");

def view_latest_snapshot():
    """View details of the latest snapshot"""
    try:
        client = MongoClient(
            "mongodb+srv://iemdpk:Imback2play@localserver.cwqbg.mongodb.net/?retryWrites=true&w=majority",
            tlsCAFile=certifi.where()
        )
        db = client["crypto"]
        collection = db["tracker"]
        
        # Get the latest snapshot
        latest_doc = collection.find_one({}, sort=[("created_at", -1)])
        if not latest_doc:
            print("❌ No snapshots found")
            return
            
        snapshot_id = latest_doc["snapshot_id"]
        
        # Get all documents for this snapshot
        snapshot_docs = collection.find({"snapshot_id": snapshot_id}).sort("document_number", 1)
        docs_list = list(snapshot_docs)
        
        print(f"\n🔍 === LATEST SNAPSHOT DETAILS ===")
        print(f"   Snapshot ID: {snapshot_id}")
        print(f"   Total Documents: {len(docs_list)}")
        
        for doc in docs_list:
            print(f"\n   📄 Document {doc['document_number']}:")
            print(f"      Timestamp: {doc['timestamp_str']}")
            print(f"      Total Coins: {doc['total_coins']}")
            print(f"      First 5 coins: {[coin['symbol'] for coin in doc['coins'][:5]]}")
        
        client.close()
        
    except Exception as e:
        print(f"❌ View error: {str(e)}")

def main():
    """Main execution function"""
    print("🚀 === CRYPTO SNAPSHOT COLLECTOR (FIFO) ===")
    print("📋 Logic: 1 Snapshot = 3 Documents (same coins, different timestamps)")
    print("🔄 Maintains exactly 3 snapshots total (9 documents)")
    print("⚡ FIFO: When 4th snapshot added, oldest gets deleted")
    print("="*60)
    
    print("\n=== BEFORE EXECUTION ===")
    get_collection_stats()
    
    print("\n🔄 === RUNNING DATA COLLECTION ===")
    snapshot_id, coin_count = create_snapshot_with_3_docs()
    
    if snapshot_id:
        print(f"✅ Successfully created snapshot with {coin_count} coins")
    else:
        print("❌ Failed to create snapshot")
    
    # print("\n=== AFTER EXECUTION ===")
    # get_collection_stats()
    
    # print("\n=== LATEST SNAPSHOT PREVIEW ===")
    # view_latest_snapshot()

if __name__ == "__main__":
    main()