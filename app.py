import streamlit as st
import requests
import pandas as pd
import numpy as np

st.set_page_config(page_title="تحليل العملات الرقمية بالعربي", layout="wide")
st.title("أفضل 10 عملات مع التحليل الفني الحقيقي (CoinGecko)")

COINGECKO_API = "https://api.coingecko.com/api/v3/coins/markets"
PARAMS = {
    "vs_currency": "usd",
    "order": "market_cap_desc",
    "per_page": 30,   # أعلى 30 عملة
    "page": 1,
    "sparkline": False
}

# ------------------------
def fetch_data():
    try:
        response = requests.get(COINGECKO_API, params=PARAMS, timeout=10)
        response.raise_for_status()
        data = response.json()
        df = pd.DataFrame(data)
        return df
    except Exception as e:
        st.error(f"حدث خطأ في الاتصال بـ CoinGecko: {e}")
        return pd.DataFrame()

# ------------------------
def fetch_historical_prices(coin_id, days=14):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {"vs_currency": "usd", "days": days}
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        prices = [p[1] for p in data['prices']]  # نجيب أسعار الإغلاق
        return pd.Series(prices)
    except:
        return pd.Series([])

# ------------------------
def calculate_ema(series, period=14):
    return series.ewm(span=period, adjust=False).mean().iloc[-1] if not series.empty else None

def calculate_rsi(series, period=14):
    if series.empty:
        return None
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean().iloc[-1]
    avg_loss = loss.rolling(period).mean().iloc[-1]
    if avg_loss == 0:
        return 100
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

# ------------------------
def calculate_score(row):
    score = 0
    if row['rsi'] is not None:
        if row['rsi'] < 30:
            score += 2
        elif row['rsi'] < 50:
            score += 1
    if row['price'] > row['ema']:
        score += 2
    if row['total_volume'] > row['total_volume']*0.8:  # حجم تداول عالي نسبي
        score += 1
    # الحيتان مش موجودة في CoinGecko → Score إضافي يمكن مستقبلي
    return score

# ------------------------
if st.button("تحديث البيانات"):
    df = fetch_data()
    if not df.empty:
        df['ema'] = None
        df['rsi'] = None
        for idx, row in df.iterrows():
            prices = fetch_historical_prices(row['id'], days=14)
            df.at[idx, 'ema'] = calculate_ema(prices)
            df.at[idx, 'rsi'] = calculate_rsi(prices)

        df['Score'] = df.apply(calculate_score, axis=1)
        df = df.sort_values(by='Score', ascending=False).head(10)

        for i, row in df.iterrows():
            st.subheader(f"{row['name']} ({row['symbol'].upper()})")
            st.write(f"**السعر الحالي:** ${row['current_price']}")
            st.write(f"**EMA آخر 14 يوم:** {row['ema']:.2f}" if row['ema'] else "EMA غير متوفر")
            st.write(f"**RSI آخر 14 يوم:** {row['rsi']:.2f}" if row['rsi'] else "RSI غير متوفر")
            st.write(f"**حجم التداول:** {row['total_volume']}")
            st.write(f"**Score للعملة:** {row['Score']}/10")

            if row['Score'] >= 7:
                rec = "✅ مناسبة للشراء تدريجيًا"
            elif row['Score'] >= 5:
                rec = "⚠️ مناسب للشراء بحذر أو انتظار فرصة أفضل"
            else:
                rec = "⏳ انتظر أو تابع التجمع قبل الشراء"
            st.write(f"**التوصية:** {rec}")
            st.markdown("---")
    else:
        st.warning("لا توجد بيانات للعرض.")
