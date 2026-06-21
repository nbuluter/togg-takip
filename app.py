import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime, date, timedelta

# --- SAYFA VE TEMA AYARLARI ---
st.set_page_config(page_title="Togg Şarj Takibi", page_icon="⚡", layout="wide")

# Kapadokya rengi ve karanlık tema detayları
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
    st.image("araba.jpg", use_container_width=True)
except:
    st.info("ℹ️ Araba görseli için: GitHub klasörünüze 'araba.jpg' adıyla bir fotoğraf yüklediğinizde burada belirecektir.")

# --- HAFIZA (VERİTABANI) AYARLARI ---
conn = sqlite3.connect('togg_sarj_yeni.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS sarj_kayitlari
             (id INTEGER PRIMARY KEY AUTOINCREMENT, tarih TEXT, sarj_tipi TEXT, firma TEXT, 
              ucret_tipi TEXT, baslama_saati TEXT, bitis_saati TEXT, fark_saati TEXT, 
              baslangic_yuzde INTEGER, guncel_km INTEGER, kw REAL, tutar REAL)''')
conn.commit()

# --- SOL MENÜ: VERİ GİRİŞİ VE İTHALAT ---
st.sidebar.markdown("### 📥 İlk Kurulum")
if st.sidebar.button("Google Sheets'ten Verileri Getir"):
    csv_url = "https://docs.google.com/spreadsheets/d/1TfZkjxQv6PO5kiAMf5hIGiC5HClfsW7m/export?format=csv&sheet=Şarj"
    try:
        eski_veri = pd.read_csv(csv_url)
        # Sütunları güvenle eşleştirip çekiyoruz
        for index, row in eski_veri.iterrows():
            st_ipi = str(row.iloc[1]) if len(row) > 1 else "AC"
            sfirma = str(row.iloc[2]) if len(row) > 2 else "Bilinmiyor"
            skw = float(row.iloc[3]) if len(row) > 3 and pd.notnull(row.iloc[3]) else 0.0
            stutar = float(row.iloc[4]) if len(row) > 4 and pd.notnull(row.iloc[4]) else 0.0
            skm = int(row.iloc[5]) if len(row) > 5 and pd.notnull(row.iloc[5]) else 0
            
            c.execute("INSERT INTO sarj_kayitlari (tarih, sarj_tipi, firma, ucret_tipi, baslama_saati, bitis_saati, fark_saati, baslangic_yuzde, guncel_km, kw, tutar) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                      (str(row.iloc[0]), st_ipi, sfirma, "Ücretli", "16:00", "17:00", "1 saat 0 dk", 20, skm, skw, stutar))
        conn.commit()
        st.sidebar.success("✅ Eski veriler başarıyla yüklendi! Sayfayı yenileyin.")
    except Exception as e:
        st.sidebar.error("Veri çekilemedi. Lütfen internet bağlantısını kontrol edin.")

st.sidebar.divider()
st.sidebar.header("🔌 Yeni Şarj Ekle")

with st.sidebar.form("yeni_kayit_formu"):
    f_tarih = st.date_input("Tarih (Gün/Ay/Yıl)", date.today())
    f_sarj_tipi = st.selectbox("Şarj Tipi", ["AC", "DC", "AC-Acil Osgb", "Hediye Şarj"])
    f_firma = st.text_input("Firma Adı (Örn: ZES, Trugo)")
    f_ucret_tipi = st.selectbox("Ücret Tipi", ["Ücretli", "Ücretsiz", "Hediye"])
    
    col1, col2 = st.columns(2)
    with col1:
        f_baslama = st.time_input("Başlangıç Saati")
    with col2:
        f_bitis = st.time_input("Bitiş Saati")
        
    f_baslangic_yuzde = st.slider("Başlangıç Enerji Yüzde Miktarı (%)", 0, 100, 20)
    f_km = st.number_input("Güncel Kilometre (Km)", min_value=0, step=1)
    f_kw = st.number_input("Alınan Miktar (kW)", min_value=0.0, format="%.2f")
    f_tutar = st.number_input("Ödenen Tutar (TL)", min_value=0.0, format="%.2f")
    
    kaydet_btn = st.form_submit_button("Sisteme Kaydet")
    
    if kaydet_btn:
        # Otomatik Fark Saati Hesaplama
        t1 = datetime.combine(date.min, f_baslama)
        t2 = datetime.combine(date.min, f_bitis)
        fark = t2 - t1
        if fark.days < 0:
            fark += timedelta(days=1)
        toplam_dakika = int(fark.total_seconds() / 60)
        fark_saat_metni = f"{toplam_dakika // 60} saat {toplam_dakika % 60} dk"
        
        c.execute("INSERT INTO sarj_kayitlari (tarih, sarj_tipi, firma, ucret_tipi, baslama_saati, bitis_saati, fark_saati, baslangic_yuzde, guncel_km, kw, tutar) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                  (f_tarih.strftime("%d/%m/%Y"), f_sarj_tipi, f_firma, f_ucret_tipi, str(f_baslama)[:5], str(f_bitis)[:5], fark_saat_metni, f_baslangic_yuzde, f_km, f_kw, f_tutar))
        conn.commit()
        st.sidebar.success("🚀 Yeni şarj kaydı başarıyla eklendi!")

# --- 2. VERİLERİ İŞLEME VE KARTLAR ---
df = pd.read_sql_query("SELECT * FROM sarj_kayitlari", conn)

if not df.empty:
    # Hesaplamalar
    toplam_kw = df['kw'].sum()
    toplam_tutar = df['tutar'].sum()
    ucretli_kw = df[df['ucret_tipi'] == 'Ücretli']['kw'].sum()
    ucretsiz_kw = df[df['ucret_tipi'].isin(['Ücretsiz', 'Hediye'])]['kw'].sum()
    
    # Performans km/TL hesabı
    km_verileri = df[df['guncel_km'] > 0]['guncel_km']
    if len(km_verileri) >= 2:
        toplam_yol = km_verileri.max() - km_verileri.min()
        ort_km_tl = toplam_tutar / toplam_yol if toplam_yol > 0 else 0.0
    else:
        ort_km_tl = 0.0

    # Tiplere göre ayırma
    dc_df = df[df['sarj_tipi'] == 'DC']
    ac_df = df[df['sarj_tipi'] == 'AC']
    osgb_df = df[df['sarj_tipi'] == 'AC-Acil Osgb']

    st.markdown("### 📊 Ana Ekran Özet Kartları")
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Toplam kW", f"{toplam_kw:.2f} kW")
    c2.metric("Toplam Tutar", f"₺{toplam_tutar:.2f}")
    c3.metric("Ücretli Alınan kW", f"{ucretli_kw:.2f} kW")
    c4.metric("Ücretsiz/Hediye kW", f"{ucretsiz_kw:.2f} kW")
    
    c5, c6, c7, c8 = st.columns(4)
    c5.metric("Ort. km/TL (Performans)", f"₺{ort_km_tl:.2f} / km")
    c6.metric("DC Toplam", f"{dc_df['kw'].sum():.2f} kW / ₺{dc_df['tutar'].sum():.2f}")
    c7.metric("AC Toplam", f"{ac_df['kw'].sum():.2f} kW / ₺{ac_df['tutar'].sum():.2f}")
    c8.metric("AC-Acil Osgb", f"{osgb_df['kw'].sum():.2f} kW / ₺{osgb_df['tutar'].sum():.2f}")

    st.divider()

    # --- 3. GRAFİKLER ---
    st.markdown("### 📈 Grafiksel Analizler")
    
    g1, g2 = st.columns(2)
    with g1:
        # Pasta Grafiği
        fig1 = px.pie(df, values='kw', names='sarj_tipi', title="AC / DC / AC-Acil Osgb Dağılımı", hole=0.3)
        st.plotly_chart(fig1, use_container_width=True)
        
        # Firmalara Göre kW
        fig2 = px.bar(df.groupby('firma')['kw'].sum().reset_index(), x='firma', y='kw', title="Firmalara Göre Alınan Enerji (kW)")
        st.plotly_chart(fig2, use_container_width=True)
        
        # Aylara Göre kW
        df['Ay'] = pd.to_datetime(df['tarih'], errors='coerce').dt.strftime('%m/%Y').fillna("Diğer")
        fig4 = px.bar(df.groupby('Ay')['kw'].sum().reset_index(), x='Ay', y='kw', title="Aylara Göre Alınan Enerji (kW)")
        st.plotly_chart(fig4, use_container_width=True)

    with g2:
        st.write("") # Boşluk ayarı
        st.write("")
        
        # Firmalara Göre TL
        fig3 = px.bar(df.groupby('firma')['tutar'].sum().reset_index(), x='firma', y='tutar', title="Firmalara Göre Harcanan Tutar (TL)")
        st.plotly_chart(fig3, use_container_width=True)
        
        # Aylara Göre TL
        fig5 = px.bar(df.groupby('Ay')['tutar'].sum().reset_index(), x='Ay', y='tutar', title="Aylara Göre Harcanan Tutar (TL)")
        st.plotly_chart(fig5, use_container_width=True)

    # --- 4. VERİ İNDİRME DOSYASI ---
    st.divider()
    st.markdown("### 📥 Veri Yedekleme ve Raporlama")
    csv_data = df.to_csv(index=False).encode('utf-8')
    st.download_button(label="📥 Tüm Verileri Telefona CSV Dosyası Olarak İndir", data=csv_data, file_name="togg_sarj_verileri.csv", mime="text/csv")

else:
    st.info("ℹ️ Uygulama hafızası şu an boş. Sol menüdeki 'Google Sheets'ten Verileri Getir' butonuna basarak eski verilerinizi tek seferlik yükleyebilirsiniz.") 
