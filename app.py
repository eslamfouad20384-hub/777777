import streamlit as st
import requests
import pandas as pd

# ------------------------
# حط مفتاحك هنا
API_KEY = "003f560175ff433399210b1564343f34"
BASE_URL = "https://api.yourcryptodata.com"  # استبدل بالرابط الصح للـ API بتاعك

# ------------------------
st.set_page_config(page_title="تحليل العملات الرقمية بالعربي", layout="wide")
st.title("أفضل 10 عملات يوميًا مع التحليل الفني")

# ------------------------
@st.cache_data(ttl=300)
def fetch_data():
    headers = {"Authorization": f"Bearer {API_KEY}"}
    response = requests.get(f"{BASE_URL}/all-coins", headers=headers)
    data = response.json()
    df = pd.DataFrame(data)
    return df

# ------------------------
df = fetch_data()

# ------------------------
# حساب Score مبسط (ممكن تزود مؤشرات)
def calculate_score(row):
    score = 0
    # RSI
    if row['rsi'] < 30:
        score += 2
    elif row['rsi'] < 50:
        score += 1
    # EMA اتجاه
    if row['ema_trend'] == 'صاعد':
        score += 2
    # حجم التداول
    if row['volume'] > row['avg_volume']:
        score += 1
    # تجمع الحيتان
    if row['whale_activity'] == 'تجمع':
        score += 2
    return score

df['Score'] = df.apply(calculate_score, axis=1)
df = df.sort_values(by='Score', ascending=False).head(10)

# ------------------------
# عرض النتائج بالعربي
for i, row in df.iterrows():
    st.subheader(f"{row['name']} ({row['symbol']})")
    st.write(f"**السعر الحالي:** {row['price']}")
    st.write(f"**الاتجاه العام:** {row['ema_trend']}")
    st.write(f"**الدعم:** {row['support']} | **المقاومة:** {row['resistance']}")
    st.write(f"**RSI:** {row['rsi']}")
    st.write(f"**حجم التداول:** {row['volume']}")
    st.write(f"**حركة الحيتان:** {row['whale_activity']}")
    st.write(f"**Score للعملة:** {row['Score']}/10")

    # توصية بالعربي
    if row['Score'] >= 7:
        rec = "✅ مناسبة للشراء تدريجيًا"
    elif row['Score'] >= 5:
        rec = "⚠️ مناسب للشراء بحذر أو انتظار فرصة أفضل"
    else:
        rec = "⏳ انتظر أو تابع التجمع قبل الشراء"
    st.write(f"**التوصية:** {rec}")
    st.markdown("---")
