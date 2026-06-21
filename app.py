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
    pass

# --- HAFIZA (VERİTABANI) AYARLARI ---
conn = sqlite3.connect('togg_sarj_nihai.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS sarj_kayitlari
             (id INTEGER PRIMARY KEY AUTOINCREMENT, tarih TEXT, sarj_tipi TEXT, firma TEXT, 
              ucret_tipi TEXT, baslama_saati TEXT, bitis_saati TEXT, fark_saati TEXT, 
              baslangic_yuzde INTEGER, guncel_km INTEGER, kw REAL, tutar REAL)''')
conn.commit()

# --- SOL MENÜ: DOSYA YÜKLEME KUTUSUNU ÇEKMECEYE SAKLADIK ---
st.sidebar.markdown("### ⚙️ Ayarlar")
with st.sidebar.expander("📥 İlk Kurulum (Dosya Yükle)", expanded=False):
    st.write("Eski verileri yüklemek için kutuyu kullanabilirsiniz. İşiniz bittiğinde bu çekmece otomatik kapanır.")
    uploaded_file = st.file_uploader("İndirdiğiniz 'SARJ.csv' dosyasını buraya bırakın", type=["csv"])

    if uploaded_file is not None:
        try:
            eski_veri = pd.read_csv(uploaded_file)
            eski_veri.columns = eski_veri.columns.str.strip().str.replace('\ufeff', '').str.replace('ï»¿', '').str.upper()
            c.execute("DELETE FROM sarj_kayitlari")
            
            def guvenli_oku(satir, aranan_isimler, varsayilan=""):
                for isim in aranan_isimler:
                    if isim in eski_veri.columns:
                        deger = satir[isim]
                        if pd.notnull(deger):
                            return str(deger).strip()
                return varsayilan

            for index, row in eski_veri.iterrows():
                try:
                    st_tarih = guvenli_oku(row, ['TARİH', 'TARIH'], date.today().strftime("%d.%m.%Y"))
                    st_tarih = st_tarih.replace('/', '.').replace('-', '.') # Eğik çizgileri noktaya çevirir
                    
                    s_tipi = guvenli_oku(row, ['ŞARJ TİPİ', 'SARJ TIPI', 'ŞARJ TIPI', 'SARJ TİPİ'], "AC")
                    sfirma = guvenli_oku(row, ['ALINAN ŞARJ FİRMASI', 'ALINAN SARJ FIRMASI', 'FİRMA'], "Bilinmiyor")
                    
                    skw_str = guvenli_oku(row, ['FATURADA ALINAN KW', 'ALINAN KW (%1=0,885 KW)', 'ALINAN KW'], "0")
                    skw = float(skw_str.replace('.', '').replace(',', '.')) if skw_str.lower() != "nan" and skw_str != "" else 0.0
                    
                    stutar_str = guvenli_oku(row, ['ÖDENEN ÜCRET', 'ODENEN UCRET', 'TUTAR'], "0")
                    if "YOK" in stutar_str.upper() or "BEDAVA" in stutar_str.upper():
                        stutar = 0.0
                        ucret_tipi = "Ücretsiz"
                    else:
                        stutar = float(stutar_str.replace('.', '').replace(',', '.')) if stutar_str.lower() != "nan" and stutar_str != "" else 0.0
                        ucret_tipi = "Ücretli"

                    skm_str = guvenli_oku(row, ['ARAÇ KM', 'ARAC KM', 'KM'], "0")
                    skm = int(float(skm_str.replace('.', '').replace(',', ''))) if skm_str.lower() != "nan" and skm_str != "" else 0

                    c.execute("INSERT INTO sarj_kayitlari (tarih, sarj_tipi, firma, ucret_tipi, baslama_saati, bitis_saati, fark_saati, baslangic_yuzde, guncel_km, kw, tutar) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                              (st_tarih, s_tipi, sfirma, ucret_tipi, "00:00", "01:00", "1 saat", 20, skm, skw, stutar))
                except:
                    continue
                    
            conn.commit()
            st.success("✅ Veriler başarıyla alındı!")
        except Exception as e:
            st.error(f"Hata: {str(e)}")

st.sidebar.divider()
st.sidebar.header("🔌 Yeni Şarj Ekle")

# --- TARİH FORMATI GÜN.AY.YIL OLARAK AYARLANDI ---
with st.sidebar.form("yeni_kayit_formu"):
    f_tarih = st.date_input("Tarih", date.today(), format="DD.MM.YYYY")
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
                  (f_tarih.strftime("%d.%m.%Y"), f_sarj_tipi, f_firma, f_ucret_tipi, str(f_baslama)[:5], str(f_bitis)[:5], fark_saat_metni, f_baslangic_yuzde, f_km, f_kw, f_tutar))
        conn.commit()
        st.sidebar.success("🚀 Yeni şarj kaydedildi!")

# --- VERİLERİ İŞLEME VE GÖSTERME ---
df = pd.read_sql_query("SELECT * FROM sarj_kayitlari", conn)

if not df.empty:
    toplam_kw = df['kw'].sum()
    toplam_tutar = df['tutar'].sum()
    
    km_verileri = df[df['guncel_km'] > 0]['guncel_km']
    ort_km_tl = toplam_tutar / (km_verileri.max() - km_verileri.min()) if len(km_verileri) >= 2 and (km_verileri.max() - km_verileri.min()) > 0 else 0.0

    st.markdown("### 📊 Ana Ekran Özet Kartları")
    c1, c2, c3 = st.columns(3)
    c1.metric("Toplam Alınan Enerji", f"{toplam_kw:,.2f} kW")
    c2.metric("Toplam Ödenen Tutar", f"₺{toplam_tutar:,.2f}")
    c3.metric("Araç Performansı (Km/TL)", f"₺{ort_km_tl:,.2f} / km")
    
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
    st.info("ℹ️ Uygulama şu an boş. Sol menüdeki 'İlk Kurulum' çekmecesini açıp 'SARJ.csv' dosyasını yükleyin.")
