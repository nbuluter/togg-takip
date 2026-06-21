import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime, date, timedelta

st.set_page_config(page_title="Togg Şarj Takibi", page_icon="⚡", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #121212; color: #FFFFFF; }
    h1, h2, h3 { color: #B59E83 !important; }
    .stButton>button { background-color: #B59E83; color: black; border-radius: 8px; font-weight: bold; width: 100%; }
    div[data-testid="stMetricValue"] { color: #B59E83 !important; font-size: 24px !important; }
    </style>
""", unsafe_allow_html=True)

st.title("⚡ Togg Şarj Takibi | 35 CTT 500")

# Veritabanı
conn = sqlite3.connect('final_togg.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS sarjlar 
             (id INTEGER PRIMARY KEY, tarih TEXT, tip TEXT, firma TEXT, kw REAL, tutar REAL, km INTEGER)''')

# Dosya Yükleme (Dosya varsa veriyi taze oku)
st.sidebar.header("📥 Veri Yükle")
uploaded_file = st.sidebar.file_uploader("SARJ.csv dosyanı bırak", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file, sep=',', encoding='utf-8')
    c.execute("DELETE FROM sarjlar")
    for _, row in df.iterrows():
        try:
            # Senin tablonun sütun isimlerine göre:
            t = str(row['TARİH'])
            tip = str(row['ŞARJ TİPİ'])
            firma = str(row['ALINAN ŞARJ FİRMASI'])
            
            # Sayısal değerleri temizle
            kw_s = str(row['ALINAN KW (%1=0,885 kW)']).replace(',','.')
            tut_s = str(row['ÖDENEN ÜCRET']).replace('ÜCRET YOK', '0').replace(',','.')
            km_s = str(row['ARAÇ KM']).replace('.','').replace(',','')
            
            kw = float(kw_s) if kw_s else 0.0
            tut = float(tut_s) if tut_s else 0.0
            km = int(float(km_s)) if km_s else 0
            
            c.execute("INSERT INTO sarjlar (tarih, tip, firma, kw, tutar, km) VALUES (?,?,?,?,?,?)", (t, tip, firma, kw, tut, km))
        except: continue
    conn.commit()
    st.rerun()

# Analiz ve Görselleştirme
df = pd.read_sql_query("SELECT * FROM sarjlar", conn)

if not df.empty:
    c1, c2, c3 = st.columns(3)
    c1.metric("Toplam Harcama", f"₺ {df['tutar'].sum():,.2f}")
    c2.metric("Toplam kW", f"{df['kw'].sum():,.2f} kW")
    c3.metric("Ortalama Tutar", f"₺ {df['tutar'].sum()/df['kw'].sum():,.2f} / kW")

    # Grafik 1: Şarj Tipi
    fig1 = px.pie(df, values='kw', names='tip', title="Şarj Tipi Dağılımı (kW)")
    
    # Grafik 2: Firma Bazlı
    fig2 = px.bar(df.groupby('firma')[['kw', 'tutar']].sum().reset_index(), x='firma', y='kw', title="Firmalara Göre Enerji")
    
    st.plotly_chart(fig1, use_container_width=True)
    st.plotly_chart(fig2, use_container_width=True)
    
    st.dataframe(df, use_container_width=True)
