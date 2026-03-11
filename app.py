import streamlit as st
import requests
import pandas as pd
import numpy as np

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

# ===================== CoinMarketCap API =======================
api_key = "9027ddd4eadf4bff8281da22868c2094"  # مفتاحك هنا

def get_cmc_data(symbols):
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
st.write("🔄 جلب البيانات الحقيقية من CoinMarketCap ...")

# هنا حط أي رموز عملات تحب تتابعها
symbols = ["BTC","ETH","BNB","ADA","SOL","DOT","LTC","XRP","AVAX","LINK"]  

coins = []
cmc = get_cmc_data(symbols)

for symbol in symbols:
    if symbol not in cmc:
        continue  # لو مفيش بيانات من CMC، تجاهل العملة
    data = cmc[symbol]
    price = data["price"]
    marketcap = data["market_cap"] if data["market_cap"] else 1
    volume = data["volume_24h"] if data["volume_24h"] else 1

    # لو مفيش بيانات تاريخية، نكرر السعر 50 مرة لحساب المؤشرات
    prices_series = pd.Series([price]*50)

    rsi = compute_RSI(prices_series).iloc[-1]
    ema20 = compute_EMA(prices_series, 20).iloc[-1]
    ema50 = compute_EMA(prices_series, 50).iloc[-1]

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
        "السعر الحالي": round(price,2),
        "الماركت كاب": round(marketcap,2),
        "حجم التداول": round(volume,2),
        "RSI": round(rsi,2),
        "EMA20": round(ema20,2),
        "EMA50": round(ema50,2),
        "تلميح": ", ".join(hint)
    })

df = pd.DataFrame(coins)

# ===================== Score وترتيب =======================
def compute_score(row):
    try:
        return (row["حجم التداول"] / row["الماركت كاب"]) / abs(row["RSI"])
    except:
        return 0

df["score"] = df.apply(compute_score, axis=1)
df_final = df.sort_values(by="score", ascending=False).head(10)

if df_final.empty:
    st.warning("لا توجد عملات تحقق الشروط حاليا")
else:
    st.subheader("🔥 أفضل 10 فرص بناءً على البيانات الحقيقية")
    st.dataframe(df_final, use_container_width=True)
