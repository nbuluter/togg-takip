import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime, date

# --- GÖRÜNÜŞ (TEMA) AYARLARI ---
st.set_page_config(page_title="Togg Şarj Takibi", page_icon="⚡", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #121212; color: #FFFFFF; }
    .stButton>button { background-color: #B59E83; color: black; border-radius: 8px; font-weight: bold; }
    .stSlider>div>div>div>div { background-color: #B59E83; }
    </style>
    """, unsafe_allow_html=True)

st.title("⚡ Togg Şarj Takibi")
st.caption("35 CTT 500 | Kapadokya Togg T10X")

# --- HAFIZA (VERİTABANI) AYARLARI ---
conn = sqlite3.connect('togg_sarj.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS sarj_kayitlari
             (id INTEGER PRIMARY KEY AUTOINCREMENT, tarih TEXT, sarj_tipi TEXT, firma TEXT, 
              ucret_tipi TEXT, baslama_saati TEXT, bitis_saati TEXT, fark_dakika INTEGER, 
              baslangic_yuzde INTEGER, guncel_km INTEGER, kw REAL, tutar REAL)''')
conn.commit()

# --- YENİ VERİ EKLEME EKRANI ---
st.sidebar.header("🔌 Yeni Şarj Ekle")
with st.sidebar.form("yeni_kayit_formu"):
    f_tarih = st.date_input("Tarih", date.today())
    f_sarj_tipi = st.selectbox("Şarj Tipi", ["AC", "DC", "AC-Acil Osgb", "Hediye Şarj"])
    f_firma = st.text_input("Firma Adı (Örn: ZES)")
    f_ucret_tipi = st.selectbox("Ücret Tipi", ["Ücretli", "Ücretsiz", "Hediye"])
    
    col1, col2 = st.columns(2)
    with col1:
        f_baslama = st.time_input("Başlangıç Saati")
    with col2:
        f_bitis = st.time_input("Bitiş Saati")
        
    f_baslangic_yuzde = st.slider("Başlangıç Şarjı (%)", 0, 100, 20)
    f_km = st.number_input("Güncel Kilometre", min_value=0)
    f_kw = st.number_input("Alınan Miktar (kW)", min_value=0.0, format="%.2f")
    f_tutar = st.number_input("Ödenen Tutar (TL)", min_value=0.0, format="%.2f")
    
    kaydet_btn = st.form_submit_button("Sisteme Kaydet")
    
    if kaydet_btn:
        t1 = datetime.combine(date.min, f_baslama)
        t2 = datetime.combine(date.min, f_bitis)
        fark = (t2 - t1).total_seconds() / 60
        if fark < 0: fark += 24 * 60 
        
        c.execute("INSERT INTO sarj_kayitlari (tarih, sarj_tipi, firma, ucret_tipi, baslama_saati, bitis_saati, fark_dakika, baslangic_yuzde, guncel_km, kw, tutar) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                  (f_tarih, f_sarj_tipi, f_firma, f_ucret_tipi, str(f_baslama), str(f_bitis), int(fark), f_baslangic_yuzde, f_km, f_kw, f_tutar))
        conn.commit()
        st.sidebar.success("Kayıt Eklendi!")

# --- BİLGİLERİ GÖSTERME VE İNDİRME ---
df = pd.read_sql_query("SELECT * FROM sarj_kayitlari", conn)

if not df.empty:
    toplam_kw = df['kw'].sum()
    toplam_tutar = df['tutar'].sum()
    
    k1, k2 = st.columns(2)
    k1.metric("Toplam Alınan", f"{toplam_kw:,.2f} kW")
    k2.metric("Toplam Ödenen", f"₺{toplam_tutar:,.2f}")
    
    st.divider()
    
    # Telefondan CSV İndirme Düğmesi
    st.markdown("### 💾 Verileri Yedekle")
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Tüm Verileri Telefondan İndir (CSV)",
        data=csv,
        file_name="togg_sarj_gecmisi.csv",
        mime="text/csv"
    )
else:
    st.info("Henüz kayıt yok. Soldaki menüden ilk şarjını ekleyebilirsin.")
