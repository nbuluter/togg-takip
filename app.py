import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
from datetime import datetime, date, timedelta

# --- AYARLAR VE TEMA ---
st.set_page_config(page_title="Togg Şarj Takibi", page_icon="⚡", layout="wide")

# Kapadokya Rengi (#B59E83) ve Koyu Tema
st.markdown("""
    <style>
    .stApp { background-color: #121212; color: #FFFFFF; }
    h1, h2, h3 { color: #B59E83 !important; }
    .stButton>button { background-color: #B59E83; color: black; border-radius: 8px; font-weight: bold; width: 100%; }
    .stSlider>div>div>div>div { background-color: #B59E83; }
    div[data-testid="stMetricValue"] { color: #B59E83 !important; }
    </style>
""", unsafe_allow_html=True)

# --- VERİTABANI ---
conn = sqlite3.connect('togg_sarj.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS kayitlar 
             (id INTEGER PRIMARY KEY, tarih TEXT, tip TEXT, firma TEXT, ucret_tipi TEXT, 
              baslangic_saat TEXT, bitis_saat TEXT, fark_saat TEXT, bas_yuzde INTEGER, 
              bit_yuzde INTEGER, fark_yuzde INTEGER, hesaplanan_kw REAL, fatura_kw REAL, 
              kw_ucreti REAL, odenen_tutar REAL, wltp INTEGER, profil INTEGER, aciklama TEXT)''')
conn.commit()

st.title("⚡ Togg Şarj Takibi | 35 CTT 500")

# --- ANA EKRAN GÖRSELİ ---
try:
    st.image("araba.jpg", use_container_width=True)
except:
    st.info("Araba görseli 'araba.jpg' olarak klasöre eklenmelidir.")

# --- YENİ KAYIT FORMU ---
with st.sidebar.expander("🔌 Yeni Şarj Ekle", expanded=False):
    with st.form("kayit_formu"):
        f_tarih = st.date_input("Tarih")
        f_tip = st.selectbox("Şarj Tipi", ["AC", "DC", "AC-Acil Osgb", "Hediye şarj"])
        f_firma = st.text_input("Firma Adı")
        f_ucret_tipi = st.selectbox("Ücret Tipi", ["Ücretli", "Ücretsiz", "Hediye"])
        
        col1, col2 = st.columns(2)
        f_bas = col1.time_input("Başlangıç Saati")
        f_bit = col2.time_input("Bitiş Saati")
        
        f_bas_y = st.slider("Başlangıç Enerji (%)", 0, 100, 20)
        f_bit_y = st.slider("Bitiş Enerji (%)", 0, 100, 80)
        
        f_fatura_kw = st.number_input("Faturada Alınan kW", format="%.2f")
        f_kw_ucreti = st.number_input("kW Ücreti (TL)", format="%.2f")
        f_odenen = st.number_input("Ödenen Ücret (TL)", format="%.2f")
        f_wltp = st.number_input("WLTP Menzil", step=1)
        f_profil = st.number_input("Profil Menzil", step=1)
        f_aciklama = st.text_area("Açıklama")
        
        # Otomatik Hesaplamalar
        fark_dakika = int((datetime.combine(date.today(), f_bit) - datetime.combine(date.today(), f_bas)).total_seconds() / 60)
        fark_saat_metni = f"{fark_dakika // 60} saat {fark_dakika % 60} dk"
        fark_yuzde = f_bit_y - f_bas_y
        hesaplanan_kw = fark_yuzde * 0.885
        
        if st.form_submit_button("KAYDET"):
            c.execute("INSERT INTO kayitlar VALUES (NULL,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                      (str(f_tarih), f_tip, f_firma, f_ucret_tipi, str(f_bas), str(f_bit), fark_saat_metni, 
                       f_bas_y, f_bit_y, fark_yuzde, hesaplanan_kw, f_fatura_kw, f_kw_ucreti, f_odenen, f_wltp, f_profil, f_aciklama))
            conn.commit()
            st.success("Kayıt Başarılı!")

# --- VERİLERİ ÇEK VE GÖSTER ---
df = pd.read_sql_query("SELECT * FROM kayitlar", conn)

if not df.empty:
    # Kartlar
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Toplam kW", f"{df['fatura_kw'].sum():.2f}")
    c2.metric("Toplam Tutar", f"{df['odenen_tutar'].sum():.2f}")
    c3.metric("Ücretli kW", f"{df[df['ucret_tipi']=='Ücretli']['fatura_kw'].sum():.2f}")
    c4.metric("Ort. km/TL", f"{ (df['odenen_tutar'].sum() / df['fatura_kw'].sum()) if df['fatura_kw'].sum()>0 else 0:.2f}")

    st.divider()
    
    # Grafikler
    g1, g2 = st.columns(2)
    fig1 = px.pie(df, values='fatura_kw', names='tip', title="Şarj Tipi Dağılımı")
    g1.plotly_chart(fig1, use_container_width=True)
    
    fig2 = px.bar(df, x='firma', y='fatura_kw', title="Firmalara Göre kW")
    g2.plotly_chart(fig2, use_container_width=True)

    st.subheader("📋 Tüm Veriler")
    st.dataframe(df)
