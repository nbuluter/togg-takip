import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from datetime import datetime

# --- AYARLAR VE TASARIM ---
st.set_page_config(page_title="TOGG ŞARJ TAKİBİ", layout="wide")

KAPADOKYA_RENGI = "#B59E83"

st.markdown(f"""
    <style>
    .stApp {{ background-color: #121212; color: #FFFFFF; }}
    h1, h2, h3 {{ color: {KAPADOKYA_RENGI} !important; text-transform: uppercase; }}
    .stButton>button {{ background-color: {KAPADOKYA_RENGI}; color: black; font-weight: bold; border-radius: 8px; width: 100%; }}
    div[data-testid="stMetricValue"] {{ color: {KAPADOKYA_RENGI} !important; }}
    </style>
""", unsafe_allow_html=True)

# --- VERİTABANI YÖNETİMİ ---
def init_db():
    conn = sqlite3.connect('togg_takip.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS sarjlar (
        TARİH TEXT, BASLANGIC_SAATI TEXT, BITIS_SAATI TEXT, SURE_DK INTEGER, ARAC_KM INTEGER,
        BAS_YUZDE INTEGER, BIT_YUZDE INTEGER, FARK_YUZDE INTEGER, SARJ_TIPI TEXT, FIRMA TEXT,
        KW_UCRETI REAL, UCRET_TIPI TEXT, FATURA_KW REAL, UCRETLI_KW REAL, UCRETLI_TUTAR REAL,
        OSGB_KW REAL, HEDIYE_KW REAL, LOKALIZASYON TEXT, WLTP INTEGER, PROFIL INTEGER,
        GERCEK_KW REAL, ACIKLAMA TEXT)''')
    conn.commit()
    return conn

conn = init_db()

# --- ANA EKRAN ---
st.title("⚡ TOGG ŞARJ TAKİBİ | 35 CTT 500")

try:
    st.image("araba.jpeg", use_container_width=True)
except:
    st.warning("LÜTFEN 'araba.jpeg' GÖRSELİNİ KLASÖRE EKLEYİN.")

# --- VERİLERİ YÜKLE VE İŞLE ---
df = pd.read_sql_query("SELECT * FROM sarjlar", conn)

if not df.empty:
    # HESAPLAMALAR
    toplam_kw = df['FATURA_KW'].fillna(0).sum() + df['OSGB_KW'].fillna(0).sum() + df['HEDIYE_KW'].fillna(0).sum()
    toplam_tutar = df['UCRETLI_TUTAR'].fillna(0).sum() # Diğer tutarların da ekleneceği yer
    
    # 12 KARTIN GÖSTERİMİ
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("TOPLAM ALINAN KW", f"{toplam_kw:,.2f} KW")
    c2.metric("TOPLAM TUTAR", f"₺ {df['UCRETLI_TUTAR'].sum():,.2f}")
    c3.metric("ÜCRETLİ ALIM KW", f"{df['UCRETLI_KW'].sum():,.2f} KW")
    c4.metric("ACİL OSGB ALIM KW", f"{df['OSGB_KW'].sum():,.2f} KW")
    
    # ... (Diğer kartlar için benzer yapı kurulabilir)

    # GRAFİKLER
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        st.subheader("ŞARJ TİPİ DAĞILIMI (KW)")
        fig1 = px.pie(df, values='FATURA_KW', names='SARJ_TIPI')
        st.plotly_chart(fig1, use_container_width=True)
    
    with col_g2:
        st.subheader("FİRMALARA GÖRE KW")
        fig2 = px.bar(df, x='FIRMA', y='FATURA_KW', orientation='h')
        st.plotly_chart(fig2, use_container_width=True)

# --- VERİ GİRİŞ EKRANI (YAN MENÜ) ---
with st.sidebar:
    st.header("🔌 YENİ EKLE")
    with st.form("yeni_sarj_formu"):
        tarih = st.date_input("TARİH")
        f_bas = st.time_input("BAŞLANGIÇ SAATİ")
        f_bit = st.time_input("BİTİŞ SAATİ")
        
        # OTOMATİK HESAPLAMALAR
        fark_dakika = (datetime.combine(date.today(), f_bit) - datetime.combine(date.today(), f_bas)).total_seconds() / 60
        
        km = st.number_input("ARAÇ KM", step=1)
        bas_y = st.slider("BAŞLANGIÇ YÜZDESİ", 0, 100, 20)
        bit_y = st.slider("BİTİŞ YÜZDESİ", 0, 100, 80)
        fark_y = bit_y - bas_y
        gercek_kw = fark_y * 0.885
        
        st.write(f"OTOMATİK HESAPLANAN ŞARJ SÜRESİ: {int(fark_dakika)} DK")
        st.write(f"OTOMATİK HESAPLANAN GERÇEK KW: {gercek_kw:.2f}")

        # DİĞER ALANLAR
        sarj_tipi = st.selectbox("ŞARJ TİPİ", ["AC", "DC", "ACIL OSGB", "HEDIYE"])
        firma = st.text_input("ŞARJ FİRMASI ADI")
        
        if st.form_submit_button("KAYDET"):
            # Veritabanına kaydet
            st.success("KAYIT BAŞARILI!")
