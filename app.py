import streamlit as st
import requests
import pandas as pd
from textblob import TextBlob

st.set_page_config(layout="wide")

st.title("🧠 محلل أخبار البورصة والكريبتو")
st.write("يجمع الأخبار ويحلل تأثيرها على السوق")

# API KEY
API_KEY = "003f560175ff433399210b1564343f34"

# ==========================
# جلب الأخبار
# ==========================

def get_news():

    url = f"https://newsapi.org/v2/everything?q=crypto OR bitcoin OR ethereum OR stock market OR egypt economy&language=en&sortBy=publishedAt&pageSize=30&apiKey={API_KEY}"

    try:
        r = requests.get(url)
        data = r.json()

        if "articles" in data:
            return data["articles"]
        else:
            st.error("مفيش أخبار جت من السيرفر")
            st.write(data)
            return []

    except:
        st.error("حصل خطأ في الاتصال")
        return []

# ==========================
# تحليل المشاعر
# ==========================

def analyze_sentiment(text):

    analysis = TextBlob(text)

    score = analysis.sentiment.polarity

    if score > 0.2:
        return "📈 إيجابي"
    elif score < -0.2:
        return "📉 سلبي"
    else:
        return "⚖️ محايد"

# ==========================
# تحديد الأصل
# ==========================

def detect_asset(text):

    text = text.lower()

    if "bitcoin" in text:
        return "BTC"
    elif "ethereum" in text:
        return "ETH"
    elif "solana" in text:
        return "SOL"
    elif "crypto" in text:
        return "سوق الكريبتو"
    elif "stock" in text:
        return "الأسهم"
    elif "egypt" in text:
        return "البورصة المصرية"
    else:
        return "عام"

# ==========================
# تشغيل التحليل
# ==========================

if st.button("تحليل الأخبار الآن"):

    news = get_news()

    if len(news) == 0:
        st.stop()

    results = []

    for article in news:

        title = article.get("title", "")
        url = article.get("url", "")

        sentiment = analyze_sentiment(title)
        asset = detect_asset(title)

        results.append({
            "الأصل المتأثر": asset,
            "الخبر": title,
            "التأثير": sentiment,
            "الرابط": url
        })

    df = pd.DataFrame(results)

    st.dataframe(df, use_container_width=True)
