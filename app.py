import streamlit as st
import requests
import pandas as pd
from textblob import TextBlob

st.set_page_config(layout="wide")

st.title("🧠 محلل الأخبار بالذكاء الاصطناعي")
st.write("تحليل أخبار البورصة المصرية والعملات الرقمية")

# ===============================
# API NEWS
# ===============================

API_KEY = "YOUR_NEWSAPI_KEY"

def get_news():
    url = f"https://newsapi.org/v2/everything?q=crypto OR bitcoin OR ethereum OR egypt economy OR stock market&language=en&sortBy=publishedAt&apiKey={API_KEY}"
    r = requests.get(url).json()
    return r["articles"][:30]

# ===============================
# تحليل المشاعر
# ===============================

def analyze_sentiment(text):

    analysis = TextBlob(text)

    score = analysis.sentiment.polarity

    if score > 0.2:
        return "📈 إيجابي"
    elif score < -0.2:
        return "📉 سلبي"
    else:
        return "⚖️ محايد"

# ===============================
# تحديد الأصل
# ===============================

def detect_asset(text):

    text = text.lower()

    if "bitcoin" in text:
        return "BTC"
    if "ethereum" in text:
        return "ETH"
    if "solana" in text:
        return "SOL"
    if "crypto" in text:
        return "سوق الكريبتو"
    if "egypt" in text:
        return "البورصة المصرية"
    if "stock" in text:
        return "الأسهم"

    return "عام"

# ===============================
# تشغيل البرنامج
# ===============================

if st.button("تحليل الأخبار الآن"):

    news = get_news()

    results = []

    for article in news:

        title = article["title"]

        sentiment = analyze_sentiment(title)

        asset = detect_asset(title)

        results.append({
            "الأصل": asset,
            "الخبر": title,
            "التأثير": sentiment,
            "الرابط": article["url"]
        })

    df = pd.DataFrame(results)

    st.dataframe(df)
