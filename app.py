import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date, timedelta

# --- SAYFA VE PREMIUM TEMA AYARLARI ---
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

# --- BULUT HAFIZA (SESSION STATE) AYARLARI ---
if 'sarj_verileri' not in st.session_state:
    st.session_state['sarj_verileri'] = pd.DataFrame(columns=['Tarih', 'Şarj Tipi', 'Firma', 'kW', 'Tutar', 'Km'])

# --- REKTÖRÜ GİZLEYEN AKILLI SİSTEM ---
# Eğer hafıza boşsa kurulum kutusunu gösterir, veri yüklenince burası kaybolur!
if st.session_state['sarj_verileri'].empty:
    st.markdown("### 📥 İlk Kurulum")
    uploaded_file = st.file_uploader("İndirdiğiniz 'SARJ.csv' dosyasını buraya bırakın", type=["csv"])

    if uploaded_file is not None:
        # Türkçe karakterleri ve Excel şifrelerini çözen süper gözlük
        df_okunan = None
        for kodlama in ['utf-8-sig', 'windows-1254', 'utf-8', 'latin1']:
            try:
                uploaded_file.seek(0)
                df_okunan = pd.read_csv(uploaded_file, encoding=kodlama)
                break
            except:
                continue
        
        if df_okunan is not None:
            # Sütun isimlerini temizle ve büyüt
            df_okunan.columns = df_okunan.columns.str.strip().str.replace('\ufeff', '').str.upper()
            
            yeni_satirlar = []
            
            def sutun_bul_ve_oku(satir, alternatif_isimler, varsayilan=""):
                for isim in alternatif_isimler:
                    if isim in df_okunan.columns and pd.notnull(satir[isim]):
                        return str(satir[isim]).strip()
                return varsayilan

            for index, row in df_okunan.iterrows():
                try:
                    tarih_ham = sutun_bul_ve_oku(row, ['TARİH', 'TARIH'], date.today().strftime("%d.%m.%Y"))
                    tarih_temiz = tarih_ham.replace('/', '.').replace('-', '.')
                    
                    tip_ham = sutun_bul_ve_oku(row, ['ŞARJ TİPİ', 'SARJ TIPI', 'ŞARJ TIPI', 'SARJ TİPİ'], "AC")
                    firma_ham = sutun_bul_ve_oku(row, ['ALINAN ŞARJ FİRMASI', 'ALINAN SARJ FIRMASI', 'FİRMA'], "Bilinmiyor")
                    
                    kw_ham = sutun_bul_ve_oku(row, ['FATURADA ALINAN KW', 'ALINAN KW (%1=0,885 KW)', 'ALINAN KW'], "0")
                    kw_float = float(kw_ham.replace('.', '').replace(',', '.')) if kw_ham else 0.0
                    
                    tutar_ham = sutun_bul_ve_oku(row, ['ÖDENEN ÜCRET', 'ODENEN UCRET', 'TUTAR'], "0")
                    if "YOK" in tutar_ham.upper() or "BEDAVA" in tutar_ham.upper():
                        tutar_float = 0.0
                    else:
                        tutar_float = float(tutar_ham.replace('.', '').replace(',', '.')) if tutar_ham else 0.0
                        
                    km_ham = sutun_bul_ve_oku(row, ['ARAÇ KM', 'ARAC KM', 'KM'], "0")
                    km_int = int(float(km_ham.replace('.', '').replace(',', ''))) if km_ham else 0
                    
                    yeni_satirlar.append({
                        'Tarih': tarih_temiz,
                        'Şarj Tipi': tip_ham,
                        'Firma': firma_ham,
                        'kW': kw_float,
                        'Tutar': tutar_float,
                        'Km': km_int
                    })
                except:
                    continue
            
            if yeni_satirlar:
                st.session_state['sarj_verileri'] = pd.DataFrame(yeni_satirlar)
                st.success("✅ Tüm veriler başarıyla yüklendi!")
                st.rerun() # Sayfayı otomatik yeniler ve kutuyu gizler!

# --- SOL MENÜ: MANUEL YENİ VERİ EKLEME ---
st.sidebar.header("🔌 Yeni Şarj Ekle")
with st.sidebar.form("yeni_kayit_formu"):
    f_tarih = st.date_input("Tarih", date.today(), format="DD.MM.YYYY")
    f_sarj_tipi = st.selectbox("Şarj Tipi", ["AC", "DC", "AC-Acil Osgb"])
    f_firma = st.text_input("Firma Adı (Örn: Trugo, ZES)")
    f_km = st.number_input("Güncel Kilometre (Km)", min_value=0, step=1)
    f_kw = st.number_input("Alınan Miktar (kW)", min_value=0.0)
    f_tutar = st.number_input("Ödenen Tutar (TL)", min_value=0.0)
    
    kaydet_btn = st.form_submit_button("Sisteme Kaydet")
    
    if kaydet_btn:
        yeni_row = pd.DataFrame([{
            'Tarih': f_tarih.strftime("%d.%m.%Y"),
            'Şarj Tipi': f_sarj_tipi,
            'Firma': f_firma,
            'kW': f_kw,
            'Tutar': f_tutar,
            'Km': f_km
        }])
        st.session_state['sarj_verileri'] = pd.concat([st.session_state['sarj_verileri'], yeni_row], ignore_index=True)
        st.sidebar.success("🚀 Yeni şarj hafızaya eklendi!")
        st.rerun()

# --- 3. ANA EKRAN GÖSTERİMİ ---
df = st.session_state['sarj_verileri']

if not df.empty:
    # Hesaplamalar
    toplam_kw = df['kW'].sum()
    toplam_tutar = df['Tutar'].sum()
    
    # Performans km/TL hesabı
    km_verileri = df[df['Km'] > 0]['Km']
    ort_km_tl = toplam_tutar / (km_verileri.max() - km_verileri.min()) if len(km_verileri) >= 2 and (km_verileri.max() - km_verileri.min()) > 0 else 0.0
    ort_fiyat = toplam_tutar / toplam_kw if toplam_kw > 0 else 0.0

    st.markdown("### 📊 Ana Ekran Özet Kartları")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Toplam Ödenen Tutar", f"₺{toplam_tutar:,.2f}")
    c2.metric("Toplam Enerji", f"{toplam_kw:,.2f} kW")
    c3.metric("Ortalama Fiyat", f"₺{ort_fiyat:,.2f} / kW")
    c4.metric("Araç Performansı", f"₺{ort_km_tl:,.2f} / km")
    
    st.divider()
    
    # Başlık kırılımları tabloları
    st.markdown("### 🔋 Şarj Tiplerine Göre Dağılım")
    grup_tip = df.groupby('Şarj Tipi')[['kW', 'Tutar']].sum().reset_index()
    st.dataframe(grup_tip, use_container_width=True, hide_index=True)
    
    st.divider()
    st.markdown("### 📈 Grafiksel Analizler")
    g1, g2 = st.columns(2)
    with g1:
        st.plotly_chart(px.pie(df, values='kW', names='Şarj Tipi', title="Şarj Tipi Dağılımı (kW)", hole=0.3), use_container_width=True)
        st.plotly_chart(px.bar(df, x='Firma', y='kW', color='Şarj Tipi', title="Firmalara Göre Alınan Enerji (kW)"), use_container_width=True)
    with g2:
        st.plotly_chart(px.bar(df, x='Firma', y='Tutar', color='Şarj Tipi', title="Firmalara Göre Harcanan Tutar (TL)"), use_container_width=True)

    st.divider()
    st.markdown("### 📥 Veri Yedekleme")
    csv_data = df.to_csv(index=False).encode('utf-8')
    st.download_button(label="📥 Tüm Verileri Telefona CSV Olarak İndir", data=csv_data, file_name="togg_sarj_verileri.csv", mime="text/csv")
