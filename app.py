import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from datetime import datetime

# --- AYARLAR ---
st.set_page_config(page_title="TOGG ŞARJ TAKİBİ", layout="wide")
KAPADOKYA_RENGI = "#B59E83"

st.markdown(f"""
    <style>
    .stApp {{ background-color: #121212; color: #FFFFFF; }}
    h1, h2, h3 {{ color: {KAPADOKYA_RENGI} !important; text-transform: uppercase; }}
    </style>
""", unsafe_allow_html=True)

st.title("⚡ TOGG ŞARJ TAKİBİ | 35 CTT 500")

# --- GÜVENLİ GÖRSEL YÜKLEME ---
try:
    st.image("araba.jpg", use_container_width=True)
except:
    st.warning("⚠️ 'araba.jpg' DOSYASI BULUNAMADI. GÖRSELİ KLASÖRE EKLEYİNİZ.")

# --- DOSYAYI OTOMATİK OKU ---
@st.cache_data
def veri_yukle():
    try:
        # senin gönderdiğin son CSV yapısına göre (noktalı virgül ile)
        return pd.read_csv("SARJ.csv", sep=";")
    except:
        return None

df = veri_yukle()

if df is not None:
    # Büyük harf dönüşümü (İstek üzerine)
    df.columns = [c.upper() for c in df.columns]
    
    # KART HESAPLAMALARI
    # L: UCRETLI_ALINAN_KW, N: ACIL_OSGB_KW, P: HEDIYE_KW (Snippet'e göre)
    st.metric("TOPLAM ALINAN KW", f"{df['UCRETLI ALINAN KW'].sum() + df['ACIL OSGB\'DEN ALINAN KW'].sum() + df['HEDIYE KW'].sum():,.2f}")
    
    st.subheader("📋 TÜM VERİLER")
    st.dataframe(df)
else:
    st.error("❌ 'SARJ.csv' DOSYASI OKUNAMADI. DOSYADAN EMİN OLUN.")
