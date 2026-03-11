import streamlit as st
import requests
import pandas as pd
import numpy as np

st.set_page_config(page_title="أداة كريبتو متقدمة 🚀", layout="wide")
st.title("🚀 كاشف العملات المضغوطة قبل الانفجار مع مؤشرات RSI و EMA ومصادر احتياطية")

st.write("""
الأداة بتحلل أفضل 250 عملة رقمية وتحدد أفضل 10 فرص للشراء، مع:
- مؤشرات RSI و EMA20 و EMA50
- كشف حجم التداول المفاجئ
- تلميحات لكل عملة
- استخدام مصادر احتياطية عند فشل المصدر الأساسي
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
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.warning(f"❌ خطأ في CoinGecko: {e}")
        return []

def get_coinmarketcap_data(api_key, symbols):
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

def get_binance_data(symbol):
    url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}USDT"
    try:
        resp = requests.get(url, timeout=10).json()
        return {
            "price": float(resp["lastPrice"]),
            "volume_24h": float(resp["quoteVolume"])
        }
    except:
        return None

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

        volume_spike = False
        if not np.isnan(volume) and len(prices_series) > 0:
            avg_price_volume = np.mean(prices_series)
            volume_spike = volume > 3 * avg_price_volume

        hint = []
        if not np.isnan(rsi):
            if rsi < 30:
                hint.append("شراء قوي (RSI منخفض)")
            elif rsi > 70:
                hint.append("بيع/تراجع محتمل (RSI مرتفع)")
            else:
                hint.append("RSI معتدل")
        else:
            hint.append("RSI غير متاح")

        if not np.isnan(ema20) and not np.isnan(ema50):
            if ema20 > ema50:
                hint.append("اتجاه صعودي (EMA20 > EMA50)")
            else:
                hint.append("اتجاه هبوطي (EMA20 < EMA50)")
        else:
            hint.append("EMA غير متاح")

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
required_cols = ["العملة","الرمز","السعر الحالي","الماركت كاب","حجم التداول",
                 "تغير السعر 24h %","RSI","EMA20","EMA50","تلميح"]

for col in required_cols:
    if col not in df.columns:
        df[col] = np.nan

df_filtered = df.dropna(subset=["الماركت كاب", "تغير السعر 24h %"])
df_filtered = df_filtered[(df_filtered["الماركت كاب"] < 500_000_000) & (df_filtered["تغير السعر 24h %"].abs() < 5)]

# ===================== حساب Score =======================
def compute_safe_score(row):
    rsi_val = row["RSI"] if not pd.isna(row["RSI"]) else 50
    try:
        return (row["حجم التداول"] / row["الماركت كاب"]) / abs(rsi_val)
    except:
        return 0

df_filtered["score"] = df_filtered.apply(compute_safe_score, axis=1)

# ===================== تحديث التلميح =======================
def compute_hint(row):
    hint = []
    if not pd.isna(row["RSI"]):
        if row["RSI"] < 30:
            hint.append("شراء قوي (RSI منخفض)")
        elif row["RSI"] > 70:
            hint.append("بيع/تراجع محتمل (RSI مرتفع)")
        else:
            hint.append("RSI معتدل")
    else:
        hint.append("RSI غير متاح")

    if not pd.isna(row["EMA20"]) and not pd.isna(row["EMA50"]):
        if row["EMA20"] > row["EMA50"]:
            hint.append("اتجاه صعودي (EMA20 > EMA50)")
        else:
            hint.append("اتجاه هبوطي (EMA20 < EMA50)")
    else:
        hint.append("EMA غير متاح")

    if not pd.isna(row["حجم التداول"]) and not pd.isna(row["الماركت كاب"]):
        if row["حجم التداول"] > 3*row["الماركت كاب"]*0.01:
            hint.append("حجم تداول مفاجئ ↑")
    return ", ".join(hint)

df_filtered["تلميح"] = df_filtered.apply(compute_hint, axis=1)

# ===================== أفضل 10 فرص =======================
df_final = df_filtered.sort_values(by="score", ascending=False).head(10)

if df_final.empty:
    st.warning("لا توجد عملات تحقق الشروط حاليا")
else:
    st.subheader("🔥 أفضل 10 فرص مضغوطة قبل الانفجار")
    st.dataframe(df_final[required_cols + ["score"]], use_container_width=True)

st.write("📊 البيانات مأخوذة أساسًا من CoinGecko، مع إمكانية استخدام مصادر احتياطية مثل CoinMarketCap وBinance عند الحاجة.")
