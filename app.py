import streamlit as st
import requests
import pandas as pd
import numpy as np

st.set_page_config(page_title="Crypto أفضل فرص شراء", layout="wide")
st.title("🚀 كاشف العملات مع Score + ترتيب الأفضل للشراء")

# ===================== دوال المؤشرات =======================
def compute_RSI(prices, period=14):
    delta = prices.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def compute_EMA(prices, period=20):
    return prices.ewm(span=period, adjust=False).mean()

# ===================== CryptoCompare =======================
def get_crypto_compare_history(symbol, limit=60, api_key="YOUR_API_KEY"):
    url = "https://min-api.cryptocompare.com/data/v2/histoday"
    params = {"fsym": symbol, "tsym": "USD", "limit": limit, "api_key": api_key}
    try:
        resp = requests.get(url, params=params, timeout=10).json()
        data = resp.get("Data", {}).get("Data", [])
        if not data:
            return None
        df = pd.DataFrame(data)
        df["close"] = df["close"].astype(float)
        df["volume"] = df["volumeto"].astype(float)
        return df
    except:
        return None

# ===================== العملات =======================
symbols = ["BTC","ETH","BNB","ADA","SOL","DOT","XRP","MATIC","LINK","AVAX"]
api_key_crypto_compare = "ضع_هنا_API_Key_من_CryptoCompare"

results = []

for sym in symbols:
    df_hist = get_crypto_compare_history(sym, limit=60, api_key=api_key_crypto_compare)
    if df_hist is None or df_hist.empty:
        continue

    prices = df_hist["close"]
    volumes = df_hist["volume"]

    rsi = compute_RSI(prices).iloc[-1]
    ema20 = compute_EMA(prices, 20).iloc[-1]
    ema50 = compute_EMA(prices, 50).iloc[-1]
    current_price = prices.iloc[-1]
    current_volume = volumes.iloc[-1]

    # ===================== التلميحات =======================
    hint = []
    if rsi < 30:
        hint.append("🟢 RSI منخفض → شراء")
    elif rsi > 70:
        hint.append("🔴 RSI مرتفع → بيع محتمل")
    else:
        hint.append("🟡 RSI معتدل")

    if ema20 > ema50:
        hint.append("📈 اتجاه صعودي")
    else:
        hint.append("📉 اتجاه هبوطي")

    results.append({
        "العملة": sym,
        "السعر الحالي": round(current_price,2),
        "RSI": round(rsi,2),
        "EMA20": round(ema20,2),
        "EMA50": round(ema50,2),
        "حجم التداول": round(current_volume,2),
        "تلميح": ", ".join(hint)
    })

df = pd.DataFrame(results)

# ===================== حساب Score =======================
if not df.empty:
    # Score = حجم التداول / EMA50 * (100 - RSI) → كلما كان أفضل للشراء، Score أعلى
    df["score"] = (df["حجم التداول"] / df["EMA50"].replace(0,1)) * (100 - df["RSI"])
    df_final = df.sort_values(by="score", ascending=False)
    
    st.subheader("🔥 أفضل العملات للشراء بناءً على Score")
    st.dataframe(df_final, use_container_width=True)
else:
    st.warning("⚠️ مفيش بيانات كافية من CryptoCompare")
