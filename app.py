import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px

st.set_page_config(layout="wide")

# Veritabanı
conn = sqlite3.connect('togg_final.db', check_same_thread=False)
c = conn.cursor()
c.execute("CREATE TABLE IF NOT EXISTS sarjlar (tarih TEXT, firma TEXT, kw REAL, tutar REAL, km INTEGER)")

st.title("⚡ Togg Şarj Takip Paneli")

# Araba Görseli
try:
    st.image("araba.jpeg", use_container_width=True)
except:
    st.info("araba.jpeg yüklemediniz.")

# Dosya Yükle
uploaded_file = st.sidebar.file_uploader("SARJ.csv yükle", type=["csv"])
if uploaded_file:
    # Dosyayı oku ve tırnaklardan/virgüllerden temizle
    df = pd.read_csv(uploaded_file)
    c.execute("DELETE FROM sarjlar")
    for _, r in df.iterrows():
        # Veriyi temizle ve sayıya çevir
        kw_str = str(r['ALINAN KW (%1=0,885 kW)']).replace('"', '').replace(',', '.')
        tut_str = str(r['ÖDENEN ÜCRET']).replace('"', '').replace(',', '.').replace('ÜCRET YOK', '0')
        km_str = str(r['ARAÇ KM']).replace('"', '').replace('.', '').replace(',', '')
        
        c.execute("INSERT INTO sarjlar VALUES (?,?,?,?,?,?)", 
                  (str(r['TARİH']), str(r['ALINAN ŞARJ FİRMASI']), float(kw_str), float(tut_str), int(km_str)))
    conn.commit()
    st.rerun()

# Verileri Çek
df = pd.read_sql_query("SELECT * FROM sarjlar", conn)

if not df.empty:
    # Metrikler
    c1, c2, c3 = st.columns(3)
    c1.metric("Toplam Harcama", f"₺{df['tutar'].sum():,.2f}")
    c2.metric("Toplam kW", f"{df['kw'].sum():,.2f} kW")
    c3.metric("Performans", f"₺{df['tutar'].sum()/(df['km'].max()-df['km'].min()):.2f} / km")

    # Grafik
    fig = px.bar(df.groupby('firma')['kw'].sum().reset_index(), x='firma', y='kw', title="Firmalara Göre Enerji")
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(df, use_container_width=True)
