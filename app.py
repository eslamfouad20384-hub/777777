import streamlit as st
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

st.set_page_config(page_title="أداة كريبتو حقيقية 🚀", layout="wide")
st.title("🚀 كاشف العملات الرقمية مع مؤشرات حقيقية (RSI, EMA)")

# ===================== دوال المؤشرات =======================
def compute_RSI(prices, period=14):
    delta = prices.diff()
    gain = delta.clip(lower=0)
    loss = -1*delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def compute_EMA(prices, period=20):
    return prices.ewm(span=period, adjust=False).mean()

# ===================== Binance API =======================
def get_binance_klines(symbol, interval="1d", limit=100):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}USDT&interval={interval}&limit={limit}"
    try:
        data = requests.get(url, timeout=10).json()
        df = pd.DataFrame(data, columns=[
            "Open time","Open","High","Low","Close","Volume",
            "Close time","Quote asset volume","Number of trades",
            "Taker buy base asset volume","Taker buy quote asset volume","Ignore"
        ])
        df["Close"] = df["Close"].astype(float)
        df["Volume"] = df["Volume"].astype(float)
        return df
    except:
        return None

# ===================== CoinMarketCap API =======================
def get_cmc_data(api_key, symbols):
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
    headers = {"X-CMC_PRO_API_KEY": api_key}
    cmc_data = {}
    for symbol in symbols:
        try:
            resp = requests.get(url, headers=headers, params={"symbol": symbol}, timeout=10).json()
            quote = resp["data"][symbol]["quote"]["USD"]
            cmc_data[symbol] = {
                "price": quote["price"],
                "market_cap": quote["market_cap"],
                "volume_24h": quote["volume_24h"]
            }
        except:
            continue
    return cmc_data

# ===================== معالجة العملات =======================
st.write("🔄 جلب البيانات الحقيقية من Binance أو CoinMarketCap ...")
symbols = ["BTC","ETH","BNB","ADA","SOL"]  # مثال، ممكن تعمل fetch لكل العملات
api_key = "YOUR_CMC_API_KEY"  # ضع مفتاحك هنا

coins = []
for symbol in symbols:
    df_prices = get_binance_klines(symbol)
    if df_prices is not None and len(df_prices) >= 50:
        prices = df_prices["Close"]
        volume = df_prices["Volume"].iloc[-1]
        price = prices.iloc[-1]
        marketcap = np.nan  # ممكن تحط قيمة من CMC لو متاحة
    else:
        cmc = get_cmc_data(api_key, [symbol])
        if symbol in cmc:
            price = cmc[symbol]["price"]
            marketcap = cmc[symbol]["market_cap"]
            volume = cmc[symbol]["volume_24h"]
            prices = pd.Series([price]*50)  # لو مفيش بيانات تاريخية، نكرر السعر 50 مرة
        else:
            continue  # لو مفيش بيانات من أي مصدر، تجاهل العملة

    rsi = compute_RSI(prices).iloc[-1]
    ema20 = compute_EMA(prices, 20).iloc[-1]
    ema50 = compute_EMA(prices, 50).iloc[-1]

    hint = []
    if rsi < 30:
        hint.append("شراء قوي (RSI منخفض)")
    elif rsi > 70:
        hint.append("بيع/تراجع محتمل (RSI مرتفع)")
    else:
        hint.append("RSI معتدل")

    if ema20 > ema50:
        hint.append("اتجاه صعودي (EMA20 > EMA50)")
    else:
        hint.append("اتجاه هبوطي (EMA20 < EMA50)")

    coins.append({
        "العملة": symbol,
        "السعر الحالي": price,
        "الماركت كاب": marketcap,
        "حجم التداول": volume,
        "RSI": round(rsi,2),
        "EMA20": round(ema20,2),
        "EMA50": round(ema50,2),
        "تلميح": ", ".join(hint)
    })

df = pd.DataFrame(coins)

# ===================== Score وترتيب =======================
def compute_score(row):
    try:
        return (row["حجم التداول"] / (row["الماركت كاب"] if not np.isnan(row["الماركت كاب"]) else 1)) / abs(row["RSI"])
    except:
        return 0

df["score"] = df.apply(compute_score, axis=1)
df_final = df.sort_values(by="score", ascending=False).head(10)

if df_final.empty:
    st.warning("لا توجد عملات تحقق الشروط حاليا")
else:
    st.subheader("🔥 أفضل 10 فرص بناءً على البيانات الحقيقية")
    st.dataframe(df_final, use_container_width=True)
