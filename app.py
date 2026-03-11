import streamlit as st
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

st.set_page_config(page_title="كاشف العملات CMC فقط", layout="wide")
st.title("🚀 أفضل العملات مع مؤشرات حقيقية من CoinMarketCap فقط")

# ===================== دوال المؤشرات =======================
def compute_RSI(prices, period=14):
    delta = prices.diff()
    gain = np.where(delta>0, delta, 0)
    loss = np.where(delta<0, -delta, 0)
    avg_gain = pd.Series(gain).rolling(period).mean()
    avg_loss = pd.Series(loss).rolling(period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def compute_EMA(prices, period=20):
    return prices.ewm(span=period, adjust=False).mean()

# ===================== CoinMarketCap API =======================
api_key = "9027ddd4eadf4bff8281da22868c2094"

def get_cmc_historical(symbol, limit=60):
    url = f"https://pro-api.coinmarketcap.com/v1/cryptocurrency/ohlcv/historical"
    headers = {"X-CMC_PRO_API_KEY": api_key}
    time_end = datetime.utcnow()
    time_start = time_end - timedelta(days=limit)
    params = {
        "symbol": symbol,
        "time_start": time_start.strftime("%Y-%m-%d"),
        "time_end": time_end.strftime("%Y-%m-%d"),
        "interval": "daily"
    }
    try:
        data = requests.get(url, headers=headers, params=params, timeout=10).json()
        quotes = data["data"]["quotes"]
        prices = [q["quote"]["USD"]["close"] for q in quotes]
        volume = [q["quote"]["USD"]["volume"] for q in quotes]
        return pd.Series(prices), pd.Series(volume)
    except:
        return None, None

# ===================== معالجة العملات =======================
symbols = ["BTC","ETH","BNB","ADA","SOL","DOT","LINK","XRP","AVAX","MATIC"]

coins = []

st.write("🔄 جلب البيانات التاريخية من CoinMarketCap ...")

for symbol in symbols:
    prices, volume = get_cmc_historical(symbol)
    if prices is None or len(prices) < 14:
        continue

    rsi = compute_RSI(prices).iloc[-1]
    ema20 = compute_EMA(prices, 20).iloc[-1]
    ema50 = compute_EMA(prices, 50).iloc[-1]
    volume_today = volume.iloc[-1]

    hint = []
    if rsi < 30:
        hint.append("شراء قوي (RSI < 30)")
    elif rsi > 70:
        hint.append("بيع محتمل (RSI > 70)")
    else:
        hint.append("RSI معتدل")

    if ema20 > ema50:
        hint.append("اتجاه صعودي (EMA20 > EMA50)")
    else:
        hint.append("اتجاه هبوطي (EMA20 < EMA50)")

    coins.append({
        "العملة": symbol,
        "السعر الحالي": round(prices.iloc[-1],2),
        "RSI": round(rsi,2),
        "EMA20": round(ema20,2),
        "EMA50": round(ema50,2),
        "حجم التداول": round(volume_today,2),
        "تلميح": ", ".join(hint)
    })

df = pd.DataFrame(coins)

if not df.empty:
    df["score"] = (df["حجم التداول"] / df["EMA50"].replace(0,1)) * (100 - df["RSI"])
    df_final = df.sort_values(by="score", ascending=False).head(10)
    st.subheader("🔥 أفضل 10 فرص حقيقية من CoinMarketCap")
    st.dataframe(df_final, use_container_width=True)
else:
    st.warning("⚠️ مفيش عملات تحقق الشروط حاليا")
