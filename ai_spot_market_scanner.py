import streamlit as st
import requests
import pandas as pd
import numpy as np

st.set_page_config(layout="wide")

# ==============================
# إعدادات عامة
# ==============================
MIN_MARKET_CAP = 50_000_000
MIN_VOLUME = 5_000_000
TOP_LIMIT = 250  # السوق ٢٥٠ عملة
MIN_SCORE = 60
FIB_PERIOD = 50

# ==============================
# أدوات مساعدة
# ==============================
def fetch_market_list():
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {"vs_currency":"usd","order":"market_cap_desc","per_page":TOP_LIMIT,"page":1,"sparkline":False}
    data = requests.get(url, params=params).json()
    df = pd.DataFrame(data)
    df["market_cap"] = df.get("market_cap", df.get("market_cap_usd",0))
    df["total_volume"] = df.get("total_volume", df.get("total_volume_usd",0))
    return df

def fetch_ohlc(symbol):
    try:
        url = f"https://min-api.cryptocompare.com/data/v2/histohour"
        params = {"fsym":symbol.upper(),"tsym":"USDT","limit":200}
        r = requests.get(url, params=params).json()
        df = pd.DataFrame(r["Data"]["Data"])
        return df
    except:
        return None

def add_indicators(df):
    df["ema50"] = df["close"].ewm(span=50).mean()
    df["ema200"] = df["close"].ewm(span=200).mean()
    delta = df["close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()
    rs = avg_gain / avg_loss
    df["rsi"] = 100 - (100/(1+rs))
    df["macd"] = df["close"].ewm(span=12).mean() - df["close"].ewm(span=26).mean()
    df["signal"] = df["macd"].ewm(span=9).mean()
    return df

def calculate_score(df, smart_mode=False):
    latest = df.iloc[-1]
    score = 0
    if latest["rsi"]<50: score+=20
    if latest["macd"]>latest["signal"]: score+=20
    if latest["ema50"]>latest["ema200"]: score+=20
    if "volumeto" not in df.columns: df["volumeto"]=df.get("volumefrom",0)*df["close"]
    avg_vol=df["volumeto"].rolling(20).mean().iloc[-1]
    if latest["volumeto"]>avg_vol: score+=10
    if smart_mode: score+=10
    return score

def find_targets(df):
    latest_price=df.iloc[-1]["close"]
    period_high=df["high"].rolling(FIB_PERIOD).max().iloc[-1]
    period_low=df["low"].rolling(FIB_PERIOD).min().iloc[-1]
    target1=max(latest_price, period_low+(period_high-period_low)*0.618)
    target2=max(latest_price, period_low+(period_high-period_low)*1.0)
    target3=max(latest_price, period_low+(period_high-period_low)*1.5)
    return target1,target2,target3

def calculate_support_resistance(df):
    if len(df)<50: return None,None
    support=df["low"].rolling(50).min().iloc[-1]
    resistance=df["high"].rolling(50).max().iloc[-1]
    return support,resistance

# ==============================
# الواجهة
# ==============================
st.title("AI Spot Market Scanner - أفضل 10 فرص")

smart_mode = st.checkbox("Smart Capital Mode")

if st.button("🔍 Scan Market"):
    st.info("جاري تحميل السوق وتحليل العملات...")
    market_df = fetch_market_list()
    market_df = market_df[(market_df["market_cap"]>MIN_MARKET_CAP)&(market_df["total_volume"]>MIN_VOLUME)]
    results = []
    progress = st.progress(0)
    total = len(market_df)

    for idx,row in enumerate(market_df.itertuples(),start=1):
        symbol = row.symbol.upper()
        st.write(f"⏳ جاري فحص: {symbol} ({idx}/{total})")
        ohlc = fetch_ohlc(symbol)
        if ohlc is None or len(ohlc)<100:
            st.write(f"❌ {symbol} → فشل جلب بيانات OHLC")
            continue
        if "volumeto" not in ohlc.columns:
            ohlc["volumeto"] = ohlc.get("volumefrom",0)*ohlc["close"]

        ohlc = add_indicators(ohlc)
        score = calculate_score(ohlc, smart_mode)
        if score < MIN_SCORE:
            st.write(f"⚠ {symbol} → Score منخفض ({score})")
            continue

        target1,target2,target3 = find_targets(ohlc)
        support,resistance = calculate_support_resistance(ohlc)
        latest = ohlc.iloc[-1]
        rsi_desc = "RSI منخفض → فرصة شراء" if latest["rsi"]<50 else "RSI مرتفع → حذر"
        macd_desc = "MACD فوق Signal → اتجاه صاعد محتمل" if latest["macd"]>latest["signal"] else "MACD تحت Signal → احتمال هبوط"
        ema_desc = "EMA50 فوق EMA200 → اتجاه صاعد" if latest["ema50"]>latest["ema200"] else "EMA50 تحت EMA200 → اتجاه هابط"
        score_desc = "فرصة قوية" if score>=80 else ("فرصة متوسطة" if score>=60 else "فرصة ضعيفة")

        results.append({
            "symbol":symbol,
            "price":latest["close"],
            "score":score,
            "score_desc":score_desc,
            "target1":target1,
            "target2":target2,
            "target3":target3,
            "support":support,
            "resistance":resistance,
            "rsi_desc":rsi_desc,
            "macd_desc":macd_desc,
            "ema_desc":ema_desc
        })
        progress.progress(idx/total)

    if not results:
        st.warning("لا توجد فرص حالياً")
    else:
        # أفضل 10 عملات حسب Score
        results_df = pd.DataFrame(results).sort_values("score",ascending=False).head(10)
        st.success("أفضل 10 فرص حالياً")

        for idx,row in results_df.iterrows():
            st.subheader(f"تحليل {row['symbol']}")
            st.write(f"💰 سعر الدخول الحالي: {round(row['price'],4)}")
            st.write(f"🎯 أهداف فيبوناتشي: {round(row['target1'],4)}, {round(row['target2'],4)}, {round(row['target3'],4)}")
            st.write(f"🟢 دعم: {round(row['support'],4)}")
            st.write(f"🔴 مقاومة: {round(row['resistance'],4)}")
            st.write(f"📊 RSI: {row['rsi_desc']}")
            st.write(f"📊 MACD: {row['macd_desc']}")
            st.write(f"📊 EMA: {row['ema_desc']}")
            st.write(f"⭐ Score: {row['score']} → {row['score_desc']}")
