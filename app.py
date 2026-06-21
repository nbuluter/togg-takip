import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime, date, timedelta

# --- SAYFA VE TEMA AYARLARI ---
st.set_page_config(page_title="Togg Şarj Takibi", page_icon="⚡", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #121212; color: #FFFFFF; }
    h1, h2, h3 { color: #B59E83 !important; }
    .stButton>button { background-color: #B59E83; color: black; border-radius: 8px; font-weight: bold; width: 100%; }
    .stSlider>div>div>div>div { background-color: #B59E83; }
    div[data-testid="stMetricValue"] { color: #B59E83 !important; font-size: 24px !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("⚡ Togg Şarj Takibi")
st.caption("35 CTT 500 | Kapadokya Togg T10X")

# ARABA GÖRSELİ
try:
    st.image("araba.jpeg", use_container_width=True)
except:
    st.info("ℹ️ Araba görseli 'araba.jpeg' adıyla GitHub'da hazır.")

# --- HAFIZA (VERİTABANI) AYARLARI ---
conn = sqlite3.connect('togg_sarj_kesin.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS sarj_kayitlari
             (id INTEGER PRIMARY KEY AUTOINCREMENT, tarih TEXT, sarj_tipi TEXT, firma TEXT, 
              ucret_tipi TEXT, baslama_saati TEXT, bitis_saati TEXT, fark_saati TEXT, 
              baslangic_yuzde INTEGER, guncel_km INTEGER, kw REAL, tutar REAL)''')
conn.commit()

# --- SOL MENÜ: DOĞRUDAN DOSYA YÜKLEME ---
st.sidebar.markdown("### 📥 İlk Kurulum (Garantili Yöntem)")
uploaded_file = st.sidebar.file_uploader("İndirdiğiniz 'SARJ.csv' dosyasını buraya bırakın", type=["csv"])

if uploaded_file is not None:
    try:
        eski_veri = pd.read_csv(uploaded_file)
        c.execute("DELETE FROM sarj_kayitlari") # Mükerrer olmaması için önce temizliyoruz
        
        for index, row in eski_veri.iterrows():
            st_tarih = str(row.iloc[0]) if len(row) > 0 else date.today().strftime("%d/%m/%Y")
            s_tipi = str(row.iloc[1]) if len(row) > 1 else "AC"
            sfirma = str(row.iloc[2]) if len(row) > 2 else "Bilinmiyor"
            skw = float(row.iloc[3]) if len(row) > 3 and pd.notnull(row.iloc[3]) else 0.0
            stutar = float(row.iloc[4]) if len(row) > 4 and pd.notnull(row.iloc[4]) else 0.0
            skm = int(row.iloc[5]) if len(row) > 5 and pd.notnull(row.iloc[5]) else 0
            
            c.execute("INSERT INTO sarj_kayitlari (tarih, sarj_tipi, firma, ucret_tipi, baslama_saati, bitis_saati, fark_saati, baslangic_yuzde, guncel_km, kw, tutar) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                      (st_tarih, s_tipi, sfirma, "Ücretli", "16:00", "17:00", "1 saat 0 dk", 20, skm, skw, stutar))
        conn.commit()
        st.sidebar.success("✅ Harika! Tüm eski veriler hafızaya yüklendi. Yüklediğiniz dosyanın yanındaki Çarpı (X) işaretine basarak kutuyu temizleyebilirsiniz.")
    except Exception as e:
        st.sidebar.error("Dosya okunurken bir hata oluştu. Lütfen dosyanın içeriğini kontrol edin.")

st.sidebar.divider()
st.sidebar.header("🔌 Yeni Şarj Ekle")

with st.sidebar.form("yeni_kayit_formu"):
    f_tarih = st.date_input("Tarih", date.today())
    f_sarj_tipi = st.selectbox("Şarj Tipi", ["AC", "DC", "AC-Acil Osgb", "Hediye Şarj"])
    f_firma = st.text_input("Firma Adı")
    f_ucret_tipi = st.selectbox("Ücret Tipi", ["Ücretli", "Ücretsiz"])
    
    col1, col2 = st.columns(2)
    with col1: f_baslama = st.time_input("Başlangıç")
    with col2: f_bitis = st.time_input("Bitiş")
        
    f_baslangic_yuzde = st.slider("Başlangıç Şarjı (%)", 0, 100, 20)
    f_km = st.number_input("Güncel Kilometre (Km)", min_value=0, step=1)
    f_kw = st.number_input("Alınan Miktar (kW)", min_value=0.0)
    f_tutar = st.number_input("Ödenen Tutar (TL)", min_value=0.0)
    
    kaydet_btn = st.form_submit_button("Sisteme Kaydet")
    
    if kaydet_btn:
        t1 = datetime.combine(date.min, f_baslama)
        t2 = datetime.combine(date.min, f_bitis)
        fark = t2 - t1
        if fark.days < 0: fark += timedelta(days=1)
        toplam_dakika = int(fark.total_seconds() / 60)
        fark_saat_metni = f"{toplam_dakika // 60} saat {toplam_dakika % 60} dk"
        
        c.execute("INSERT INTO sarj_kayitlari (tarih, sarj_tipi, firma, ucret_tipi, baslama_saati, bitis_saati, fark_saati, baslangic_yuzde, guncel_km, kw, tutar) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                  (f_tarih.strftime("%d/%m/%Y"), f_sarj_tipi, f_firma, f_ucret_tipi, str(f_baslama)[:5], str(f_bitis)[:5], fark_saat_metni, f_baslangic_yuzde, f_km, f_kw, f_tutar))
        conn.commit()
        st.sidebar.success("🚀 Yeni şarj başarıyla kaydedildi!")

# --- 3. VERİLERİ İŞLEME VE GÖSTERME ---
df = pd.read_sql_query("SELECT * FROM sarj_kayitlari", conn)

if not df.empty:
    toplam_kw = df['kw'].sum()
    toplam_tutar = df['tutar'].sum()
    
    # Performans hesabı
    km_verileri = df[df['guncel_km'] > 0]['guncel_km']
    ort_km_tl = toplam_tutar / (km_verileri.max() - km_verileri.min()) if len(km_verileri) >= 2 and (km_verileri.max() - km_verileri.min()) > 0 else 0.0

    st.markdown("### 📊 Ana Ekran Özet Kartları")
    c1, c2, c3 = st.columns(3)
    c1.metric("Toplam Alınan Enerji", f"{toplam_kw:.2f} kW")
    c2.metric("Toplam Ödenen Tutar", f"₺{toplam_tutar:.2f}")
    c3.metric("Araç Performansı (Km/TL)", f"₺{ort_km_tl:.2f} / km")
    
    st.divider()
    st.markdown("### 📈 Grafiksel Analizler")
    g1, g2 = st.columns(2)
    with g1:
        st.plotly_chart(px.pie(df, values='kw', names='sarj_tipi', title="Şarj Tipi Dağılımı (kW)"), use_container_width=True)
        st.plotly_chart(px.bar(df.groupby('firma')['kw'].sum().reset_index(), x='firma', y='kw', title="Firmalara Göre Enerji (kW)"), use_container_width=True)
    with g2:
        st.plotly_chart(px.bar(df.groupby('firma')['tutar'].sum().reset_index(), x='firma', y='tutar', title="Firmalara Göre Harcama (TL)"), use_container_width=True)

    st.divider()
    csv_data = df.to_csv(index=False).encode('utf-8')
    st.download_button(label="📥 Tüm Verileri Telefona CSV Olarak İndir", data=csv_data, file_name="togg_sarj_verileri.csv", mime="text/csv")
else:
    st.info("ℹ️ Uygulama şu an boş. Sol taraftaki kutuya indirdiğiniz 'SARJ.csv' dosyasını yükleyin.")
