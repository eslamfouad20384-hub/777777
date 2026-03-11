import streamlit as st
import requests
import pandas as pd
import numpy as np

# ===========================================
st.set_page_config(page_title="أداة كريبتو بالفعل 🧠", layout="wide")
st.title("🚀 كاشف العملات بـ RSI و EMA من بيانات تاريخية حقيقية")

# ===========================================
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

# ===========================================
# Binance Historic Data (Daily)
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

# ===========================================
st.write("🔄 جلب البيانات التاريخية من Binance ...")

#  رموز العملات اللي عايز تتابعها
symbols = ["BTC","ETH","BNB","ADA","SOL","LINK","AVAX","DOT","MATIC","XRP"]

coins = []

for symbol in symbols:
    df_prices = get_binance_klines(symbol, limit=100)  # 100 يوم تاريخ
    if df_prices is None or len(df_prices) < 50:
        continue  # لو مش موجود على Binance أو ما فيش بيانات كافية

    prices = df_prices["Close"]
    volume_today = df_prices["Volume"].iloc[-1]
    price_today = prices.iloc[-1]

    # حساب المؤشرات
    rsi_series = compute_RSI(prices, 14)
    ema20_series = compute_EMA(prices, 20)
    ema50_series = compute_EMA(prices, 50)

    rsi = rsi_series.iloc[-1]
    ema20 = ema20_series.iloc[-1]
    ema50 = ema50_series.iloc[-1]

    # مؤشر حجم التداول
    avg_volume = df_prices["Volume"].rolling(14).mean().iloc[-2]  # متوسط 14 يوم قبل اليوم
    volume_spike = volume_today > 3 * avg_volume

    # تلميحات
    hint = []
    if not np.isnan(rsi):
        if rsi < 30:
            hint.append("شراء قوي (RSI < 30)")
        elif rsi > 70:
            hint.append("بيع/تراجع محتمل (RSI > 70)")
        else:
            hint.append("RSI معتدل")
    if not np.isnan(ema20) and not np.isnan(ema50):
        if ema20 > ema50:
            hint.append("اتجاه صعودي (EMA20 > EMA50)")
        else:
            hint.append("اتجاه هبوطي (EMA20 < EMA50)")
    if volume_spike:
        hint.append("حجم تداول ↑ 3 مرات")

    coins.append({
        "العملة": symbol,
        "السعر الحالي": round(price_today,2),
        "RSI": round(rsi,2),
        "EMA20": round(ema20,2),
        "EMA50": round(ema50,2),
        "حجم التداول": round(volume_today,2),
        "تلميح": ", ".join(hint)
    })

df = pd.DataFrame(coins)

# ===========================================
# Score
df["score"] = (df["حجم التداول"] / df["EMA50"].replace(0,1)) * (100 - df["RSI"])

df_final = df.sort_values(by="score", ascending=False).head(10)

if df_final.empty:
    st.warning("⚠️ مفيش عملات بتحقق الشروط أو مش موجودة على Binance")
else:
    st.subheader("🔥 أفضل 10 فرص حقيقية بالفعل")
    st.dataframe(df_final, use_container_width=True)
