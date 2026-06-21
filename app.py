import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px

st.set_page_config(layout="wide")

# Veritabanı bağlantısı (kalıcı olması için)
conn = sqlite3.connect('togg_final.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS sarjlar 
             (tarih TEXT, firma TEXT, kw REAL, tutar REAL, km INTEGER)''')
conn.commit()

st.title("⚡ Togg Şarj Takip Paneli")

# 1. Dosya Yükleme (Verileri bir kez yüklemek yeterlidir)
uploaded_file = st.sidebar.file_uploader("SARJ.csv dosyanı yükle", type=["csv"])
if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)
        c.execute("DELETE FROM sarjlar")
        
        for _, r in df.iterrows():
            # Temizlik: Virgülleri noktaya çevir, "ÜCRET YOK"u 0 yap
            try:
                kw_str = str(r['FATURADA ALINAN KW']).replace(',', '.') if pd.notnull(r['FATURADA ALINAN KW']) else "0"
                tutar_str = str(r['ÖDENEN ÜCRET']).replace('ÜCRET YOK', '0').replace(',', '.')
                km_val = int(float(str(r['ARAÇ KM']).replace('.', '').replace(',', ''))) if pd.notnull(r['ARAÇ KM']) else 0
                
                c.execute("INSERT INTO sarjlar VALUES (?,?,?,?,?)", 
                          (str(r['TARİH']), str(r['ALINAN ŞARJ FİRMASI']), float(kw_str), float(tutar_str), km_val))
            except: continue
        conn.commit()
        st.success("Veriler başarıyla yüklendi! Lütfen sayfayı yenile.")
    except Exception as e:
        st.error(f"Hata oluştu: {e}")

# 2. Verileri Çek
df = pd.read_sql_query("SELECT * FROM sarjlar", conn)

if not df.empty:
    # Metrikler
    c1, c2, c3 = st.columns(3)
    c1.metric("Toplam Harcama", f"₺{df['tutar'].sum():,.2f}")
    c2.metric("Toplam kW", f"{df['kw'].sum():,.2f} kW")
    
    # 3. Grafik
    fig = px.bar(df.groupby('firma')['kw'].sum().reset_index(), x='firma', y='kw', title="Firmalara Göre Enerji")
    st.plotly_chart(fig, use_container_width=True)
    
    # Veri Tablosu
    st.dataframe(df, use_container_width=True)
else:
    st.warning("Veri bulunamadı. Lütfen sol taraftan SARJ.csv dosyanı yükle.")
