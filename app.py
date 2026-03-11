import streamlit as st
import requests
import pandas as pd
import numpy as np

st.set_page_config(page_title="أداة كريبتو متقدمة 🚀", layout="wide")
st.title("🚀 كاشف العملات المضغوطة قبل الانفجار مع المؤشرات الفنية")

st.write("الأداة دي بتحلل أفضل 250 عملة وتطلع أفضل 10 فرص للشراء بناءً على: حجم التداول، RSI، EMA20 وEMA50، ووضع السوق العام.")

# دالة لحساب RSI
def compute_RSI(prices, period=14):
    delta = prices.diff()
    gain = delta.clip(lower=0)
    loss = -1*delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

# دالة لحساب EMA
def compute_EMA(prices, period=20):
    return prices.ewm(span=period, adjust=False).mean()

# جلب البيانات من CoinGecko
url = "https://api.coingecko.com/api/v3/coins/markets"
params = {
    "vs_currency": "usd",
    "order": "market_cap_desc",
    "per_page": 250,
    "page": 1,
    "sparkline": True  # عشان نحسب RSI و EMA
}

data = requests.get(url, params=params).json()
coins = []

for coin in data:
    try:
        name = coin["name"]
        symbol = coin["symbol"].upper()
        price = coin["current_price"]
        marketcap = coin["market_cap"]
        volume = coin["total_volume"]
        price_change = coin["price_change_percentage_24h"]
        sparkline = coin["sparkline_in_7d"]["price"]  # أسعار آخر 7 أيام

        prices_series = pd.Series(sparkline)
        rsi = compute_RSI(prices_series).iloc[-1] if len(prices_series) > 14 else None
        ema20 = compute_EMA(prices_series, 20).iloc[-1] if len(prices_series) >= 20 else None
        ema50 = compute_EMA(prices_series, 50).iloc[-1] if len(prices_series) >= 50 else None

        # زيادة حجم التداول المفاجئة
        avg_volume = np.mean(volume)
        volume_spike = volume > 3 * avg_volume

        # التلميح بناءً على المؤشرات
        hint = []
        if rsi is not None:
            if rsi < 30:
                hint.append("شراء قوي (RSI منخفض)")
            elif rsi > 70:
                hint.append("بيع/تراجع محتمل (RSI مرتفع)")
            else:
                hint.append("RSI معتدل")
        if ema20 is not None and ema50 is not None:
            if ema20 > ema50:
                hint.append("اتجاه صعودي (EMA20 > EMA50)")
            else:
                hint.append("اتجاه هبوطي (EMA20 < EMA50)")
        if volume_spike:
            hint.append("حجم تداول مفاجئ ↑")

        coins.append({
            "العملة": name,
            "الرمز": symbol,
            "السعر الحالي": price,
            "الماركت كاب": marketcap,
            "حجم التداول": volume,
            "تغير السعر 24h %": price_change,
            "RSI": round(rsi,2) if rsi is not None else None,
            "EMA20": round(ema20,2) if ema20 is not None else None,
            "EMA50": round(ema50,2) if ema50 is not None else None,
            "تلميح": ", ".join(hint)
        })
    except:
        continue

df = pd.DataFrame(coins)

# فلترة أفضل العملات: ماركت كاب < 500 مليون و تغيّر سعر < 5%
df_filtered = df[(df["الماركت كاب"] < 500_000_000) & (df["تغير السعر 24h %"].abs() < 5)]

# حساب score بسيط لترتيب الفرص
df_filtered["score"] = (df_filtered["حجم التداول"] / df_filtered["الماركت كاب"]) / (df_filtered["RSI"].replace(0,np.nan).abs())

# ترتيب على حسب score أعلى أول 10
df_final = df_filtered.sort_values(by="score", ascending=False).head(10)

st.subheader("🔥 أفضل 10 فرص مضغوطة قبل الانفجار")
st.dataframe(df_final[[
    "العملة","الرمز","السعر الحالي","الماركت كاب","حجم التداول","تغير السعر 24h %","RSI","EMA20","EMA50","تلميح"
]], use_container_width=True)

st.write("📊 بيانات مأخوذة من CoinGecko مباشرة. التلميحات مبنية على مؤشرات RSI و EMA وحجم التداول.")
