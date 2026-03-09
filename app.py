import streamlit as st
import requests
import pandas as pd
from textblob import TextBlob
from deep_translator import GoogleTranslator

st.set_page_config(layout="wide")

st.title("🧠 محلل أخبار البورصة والكريبتو")
st.write("يجمع الأخبار ويحلل تأثيرها على السوق بالعربي")

# مفتاح الأخبار
NEWS_API = "003f560175ff433399210b1564343f34"

# =========================
# جلب الأخبار العامة
# =========================

def get_general_news():

    url = f"https://newsapi.org/v2/everything?q=stock market OR egypt economy OR bitcoin OR crypto&language=en&sortBy=publishedAt&pageSize=20&apiKey={NEWS_API}"

    r = requests.get(url)
    data = r.json()

    if "articles" in data:
        return data["articles"]
    return []

# =========================
# أخبار الكريبتو
# =========================

def get_crypto_news():

    url = "https://cryptopanic.com/api/v1/posts/?auth_token=demo&public=true"

    try:
        r = requests.get(url)
        data = r.json()

        return data["results"][:20]

    except:
        return []

# =========================
# ترجمة
# =========================

def translate(text):

    try:
        return GoogleTranslator(source='auto', target='ar').translate(text)
    except:
        return text

# =========================
# تحليل المشاعر
# =========================

def analyze(text):

    score = TextBlob(text).sentiment.polarity

    if score > 0.2:
        return "📈 إيجابي", "فرصة شراء"
    elif score < -0.2:
        return "📉 سلبي", "حذر"
    else:
        return "⚖️ محايد", "انتظار"

# =========================
# تحديد الأصل
# =========================

def detect_asset(text):

    text = text.lower()

    if "bitcoin" in text:
        return "بيتكوين"
    elif "ethereum" in text:
        return "إيثريوم"
    elif "solana" in text:
        return "سولانا"
    elif "crypto" in text:
        return "سوق العملات الرقمية"
    elif "egypt" in text:
        return "البورصة المصرية"
    else:
        return "السوق العام"

# =========================
# تشغيل التحليل
# =========================

if st.button("تحليل الأخبار الآن"):

    results = []

    # الأخبار العامة
    news = get_general_news()

    for article in news:

        title = article.get("title","")
        url = article.get("url","")

        ar_title = translate(title)

        sentiment, decision = analyze(title)

        asset = detect_asset(title)

        results.append({
            "الأصل": asset,
            "الخبر": ar_title,
            "التأثير": sentiment,
            "التقييم": decision,
            "الرابط": url
        })

    # أخبار الكريبتو
    crypto_news = get_crypto_news()

    for article in crypto_news:

        title = article.get("title","")
        url = article.get("url","")

        ar_title = translate(title)

        sentiment, decision = analyze(title)

        asset = detect_asset(title)

        results.append({
            "الأصل": asset,
            "الخبر": ar_title,
            "التأثير": sentiment,
            "التقييم": decision,
            "الرابط": url
        })

    df = pd.DataFrame(results)

    st.dataframe(df, use_container_width=True)
