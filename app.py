import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px

st.set_page_config(layout="wide")

# Veritabanı bağlantısı
conn = sqlite3.connect('togg_data.db', check_same_thread=False)
c = conn.cursor()
c.execute("CREATE TABLE IF NOT EXISTS sarjlar (tarih TEXT, tip TEXT, firma TEXT, kw REAL, tutar REAL, km INTEGER)")

st.title("⚡ Togg Şarj Takip Paneli")

# Araba Görseli
try:
    st.image("araba.jpeg", use_container_width=True)
except:
    st.warning("araba.jpeg dosyası GitHub'da bulunamadı.")

# Dosya Yükleme (Veri Koruma)
uploaded_file = st.sidebar.file_uploader("SARJ.csv dosyanı yükle", type=["csv"])
if uploaded_file:
    df = pd.read_csv(uploaded_file)
    c.execute("DELETE FROM sarjlar")
    for _, r in df.iterrows():
        c.execute("INSERT INTO sarjlar VALUES (?,?,?,?,?,?)", (str(r[0]), str(r[1]), str(r[2]), float(r[3]), float(r[4]), int(r[5])))
    conn.commit()
    st.success("Veriler kalıcı olarak kaydedildi!")

# Verileri Çek
df = pd.read_sql_query("SELECT * FROM sarjlar", conn)

if not df.empty:
    # Metrikler
    c1, c2, c3 = st.columns(3)
    c1.metric("Toplam Harcama", f"₺{df['tutar'].sum():,.2f}")
    c2.metric("Toplam kW", f"{df['kw'].sum():,.2f} kW")
    c3.metric("Performans", f"₺{(df['tutar'].sum()/(df['km'].max()-df['km'].min())):.2f} / km")

    # Grafik
    fig = px.pie(df, values='kw', names='tip', title="Şarj Tipi Dağılımı")
    st.plotly_chart(fig)
else:
    st.error("Henüz veri yok! Lütfen sol menüden SARJ.csv dosyanı yükle.")

# Yeni Veri Girişi
with st.sidebar.form("yeni"):
    st.header("Yeni Kayıt")
    tarih = st.date_input("Tarih")
    tip = st.selectbox("Tip", ["AC", "DC"])
    firma = st.text_input("Firma")
    kw = st.number_input("kW")
    tutar = st.number_input("Tutar")
    km = st.number_input("Km")
    if st.form_submit_button("Kaydet"):
        c.execute("INSERT INTO sarjlar VALUES (?,?,?,?,?,?)", (tarih, tip, firma, kw, tutar, km))
        conn.commit()
        st.rerun()
