import streamlit as st
import requests
import pandas as pd
import numpy as np

st.set_page_config(page_title="أداة كريبتو متقدمة 🚀", layout="wide")
st.title("🚀 كاشف العملات المضغوطة قبل الانفجار مع مؤشرات RSI و EMA")

st.write("""
الأداة دي بتحلل أفضل 250 عملة رقمية وتحدد أفضل 10 فرص للشراء بناءً على:
- حجم التداول المفاجئ
- مؤشرات RSI و EMA20 و EMA50
- وضع السوق العام
- مصادر بيانات مزدوجة: CoinGecko + CoinMarketCap
""")

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

# ===================== جلب البيانات =======================
def get_coingecko_data():
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": 250,
        "page": 1,
        "sparkline": True,
        "price_change_percentage": "24h"
    }
    data = requests.get(url, params=params).json()
    return data

def get_coinmarketcap_data(api_key, symbols):
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
    headers = {"X-CMC_PRO_API_KEY": api_key}
    cmc_data = {}
    for symbol in symbols:
        params = {"symbol": symbol}
        try:
            resp = requests.get(url, headers=headers, params=params).json()
            quote = resp["data"][symbol]["quote"]["USD"]
            cmc_data[symbol] = {
                "price": quote["price"],
                "market_cap": quote["market_cap"],
                "volume_24h": quote["volume_24h"]
            }
        except:
            continue
    return cmc_data

# ===================== معالجة البيانات =======================
st.write("🔄 تحديث البيانات من CoinGecko ...")
data = get_coingecko_data()
coins = []

for coin in data:
    try:
        name = coin["name"]
        symbol = coin["symbol"].upper()
        price = coin.get("current_price", np.nan)
        marketcap = coin.get("market_cap", np.nan)
        volume = coin.get("total_volume", np.nan)
        change = coin.get("price_change_percentage_24h", np.nan)
        sparkline = coin.get("sparkline_in_7d", {}).get("price", [])

        prices_series = pd.Series(sparkline)
        rsi = compute_RSI(prices_series).iloc[-1] if len(prices_series) > 14 else np.nan
        ema20 = compute_EMA(prices_series, 20).iloc[-1] if len(prices_series) >= 20 else np.nan
        ema50 = compute_EMA(prices_series, 50).iloc[-1] if len(prices_series) >= 50 else np.nan

        volume_spike = volume > 3*np.mean(prices_series) if len(prices_series) > 0 else False

        # التلميح لكل عملة
        hint = []
        if not np.isnan(rsi):
            if rsi < 30:
                hint.append("شراء قوي (RSI منخفض)")
            elif rsi > 70:
                hint.append("بيع/تراجع محتمل (RSI مرتفع)")
            else:
                hint.append("RSI معتدل")
        if not np.isnan(ema20) and not np.isnan(ema50):
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
            "تغير السعر 24h %": change,
            "RSI": round(rsi,2) if not np.isnan(rsi) else np.nan,
            "EMA20": round(ema20,2) if not np.isnan(ema20) else np.nan,
            "EMA50": round(ema50,2) if not np.isnan(ema50) else np.nan,
            "تلميح": ", ".join(hint)
        })
    except:
        continue

df = pd.DataFrame(coins)

# ===================== فلترة وفرز =======================
required_cols = ["العملة","الرمز","السعر الحالي","الماركت كاب","حجم التداول","تغير السعر 24h %","RSI","EMA20","EMA50","تلميح"]
for col in required_cols:
    if col not in df.columns:
        df[col] = np.nan

df_filtered = df.dropna(subset=["الماركت كاب", "تغير السعر 24h %"])
df_filtered = df_filtered[(df_filtered["الماركت كاب"] < 500_000_000) & (df_filtered["تغير السعر 24h %"].abs() < 5)]

if df_filtered.empty:
    st.warning("لا توجد عملات تحقق الشروط حاليا")
else:
    df_filtered["score"] = (df_filtered["حجم التداول"] / df_filtered["الماركت كاب"]) / (df_filtered["RSI"].replace(0,np.nan).abs())
    df_final = df_filtered.sort_values(by="score", ascending=False).head(10)

    st.subheader("🔥 أفضل 10 فرص مضغوطة قبل الانفجار")
    st.dataframe(df_final[required_cols + ["score"]], use_container_width=True)

st.write("📊 بيانات مأخوذة من CoinGecko مباشرة، مع إمكانية استخدام CoinMarketCap كبديل عند الحاجة.")
