import streamlit as st
import requests
import pandas as pd

# ------------------------
# حط هنا رابط API بتاعك إذا موجود، لو مش موجود هشتغل على بيانات تجريبية
BASE_URL = ""  # مثال: "https://api.yourcryptodata.com/all-coins"

st.set_page_config(page_title="تحليل العملات الرقمية بالعربي", layout="wide")
st.title("أفضل 10 عملات مع التحليل الفني (تجريبي)")

# ------------------------
def fetch_data():
    # لو الرابط موجود
    if BASE_URL:
        try:
            response = requests.get(BASE_URL, timeout=10)
            response.raise_for_status()
            data = response.json()
            df = pd.DataFrame(data)
        except Exception as e:
            st.error(f"حدث خطأ في الاتصال بالـ API: {e}")
            df = pd.DataFrame()  # يرجع فارغ لو في مشكلة
    else:
        # بيانات تجريبية بدل API
        df = pd.DataFrame([
            {"name":"DOT","symbol":"DOT","price":5.2,"ema_trend":"صاعد",
             "support":5.0,"resistance":5.5,"rsi":45,"volume":1000000,"avg_volume":800000,"whale_activity":"تجمع"},
            {"name":"JST","symbol":"JST","price":0.058,"ema_trend":"هابط",
             "support":0.055,"resistance":0.062,"rsi":28,"volume":500000,"avg_volume":600000,"whale_activity":"لا تجمع"}
        ])
    return df

# ------------------------
def calculate_score(row):
    score = 0
    if row['rsi'] < 30:
        score += 2
    elif row['rsi'] < 50:
        score += 1
    if row['ema_trend'] == 'صاعد':
        score += 2
    if row['volume'] > row['avg_volume']:
        score += 1
    if row['whale_activity'] == 'تجمع':
        score += 2
    return score

# ------------------------
if st.button("تحديث البيانات"):
    df = fetch_data()
    if not df.empty:
        df['Score'] = df.apply(calculate_score, axis=1)
        df = df.sort_values(by='Score', ascending=False).head(10)

        for i, row in df.iterrows():
            st.subheader(f"{row['name']} ({row['symbol']})")
            st.write(f"**السعر الحالي:** {row['price']}")
            st.write(f"**الاتجاه العام:** {row['ema_trend']}")
            st.write(f"**الدعم:** {row['support']} | **المقاومة:** {row['resistance']}")
            st.write(f"**RSI:** {row['rsi']}")
            st.write(f"**حجم التداول:** {row['volume']}")
            st.write(f"**حركة الحيتان:** {row['whale_activity']}")
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
