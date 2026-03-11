import streamlit as st
import requests
import pandas as pd

# إعداد الصفحة
st.set_page_config(page_title="كاشف العملات قبل الانفجار", layout="wide")

st.title("🚀 كاشف العملات المضغوطة قبل الانفجار")

st.write("الأداة دي بتفحص أفضل 250 عملة في السوق وتطلع العملات اللي:")
st.write("1️⃣ حجم التداول عالي")
st.write("2️⃣ السعر لسه ثابت")
st.write("3️⃣ الماركت كاب أقل من 500 مليون")

# زر تحديث البيانات
if st.button("🔄 تحديث البيانات"):

    url = "https://api.coingecko.com/api/v3/coins/markets"

    params = {
        "vs_currency": "usd",
        "order": "volume_desc",
        "per_page": 250,
        "page": 1,
        "sparkline": False,
        "price_change_percentage": "24h"
    }

    data = requests.get(url, params=params).json()

    coins = []

    for coin in data:

        name = coin["name"]
        symbol = coin["symbol"].upper()
        price = coin["current_price"]
        volume = coin["total_volume"]
        marketcap = coin["market_cap"]
        change = coin["price_change_percentage_24h"]

        # الشروط
        if marketcap is not None and volume is not None and change is not None:

            if marketcap < 500000000 and volume > (marketcap * 0.03) and abs(change) < 5:

                coins.append({
                    "العملة": name,
                    "الرمز": symbol,
                    "السعر الحالي": price,
                    "الماركت كاب": marketcap,
                    "حجم التداول": volume,
                    "تغير السعر 24h %": round(change,2)
                })

    df = pd.DataFrame(coins)

    if len(df) > 0:
        st.success(f"تم العثور على {len(df)} عملة مرشحة")
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("لا يوجد عملات تحقق الشروط حالياً")

st.write("📊 يتم جلب البيانات من CoinGecko مباشرة")
