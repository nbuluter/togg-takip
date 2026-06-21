import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, time
import os, json, base64

# --- SAYFA AYARLARI ----------------------------------------------------------
st.set_page_config(
    page_title="TOGG ŞARJ TAKİBİ",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- KAPADOKYA RENKLERİ ------------------------------------------------------
KAPAK = "#C4A882"   # ana kapadokya bej/bronz
KAPAK_D = "#A08060" # koyu tonu
DARK_BG  = "#0F0F0F"
CARD_BG  = "#1A1A1A"
CARD2_BG = "#222222"
TEXT     = "#F5F0EA"
ACCENT   = "#C4A882"

st.markdown(f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&display=swap');

  html, body, [class*="css"] {{
    font-family: 'Inter', sans-serif;
    background-color: {DARK_BG};
    color: {TEXT};
  }}
  .stApp {{ background-color: {DARK_BG}; }}

  /* Sidebar */
  [data-testid="stSidebar"] {{ background-color: #111 !important; }}

  /* Butonlar */
  .stButton > button {{
    background-color: {KAPAK};
    color: #000;
    font-weight: 800;
    border: none;
    border-radius: 10px;
    padding: 0.6rem 1.4rem;
    font-size: 15px;
    letter-spacing: 0.5px;
    transition: all 0.2s;
  }}
  .stButton > button:hover {{
    background-color: {KAPAK_D};
    transform: translateY(-1px);
  }}

  /* Form input */
  .stTextInput>div>div>input,
  .stNumberInput>div>div>input,
  .stSelectbox>div>div,
  .stTimeInput>div>div>input {{
    background-color: {CARD2_BG} !important;
    color: {TEXT} !important;
    border: 1px solid #333 !important;
    border-radius: 8px !important;
  }}

  /* Tab */
  .stTabs [data-baseweb="tab-list"] {{
    gap: 4px;
    background: {CARD_BG};
    border-radius: 12px;
    padding: 4px;
  }}
  .stTabs [data-baseweb="tab"] {{
    background: transparent;
    color: #888;
    border-radius: 8px;
    font-weight: 600;
  }}
  .stTabs [aria-selected="true"] {{
    background: {KAPAK} !important;
    color: #000 !important;
  }}

  /* Metrikler */
  [data-testid="metric-container"] {{
    background: {CARD_BG};
    border: 1px solid #2A2A2A;
    border-radius: 12px;
    padding: 12px 16px;
  }}
  [data-testid="metric-container"] > div > div {{
    color: {KAPAK} !important;
  }}

  /* Başlıklar */
  h1, h2, h3 {{ color: {TEXT}; }}

  /* Divider */
  hr {{ border-color: #2A2A2A; }}

  /* DataFrame */
  .stDataFrame {{ border-radius: 12px; overflow: hidden; }}

  /* Scrollbar */
  ::-webkit-scrollbar {{ width: 6px; }}
  ::-webkit-scrollbar-track {{ background: {DARK_BG}; }}
  ::-webkit-scrollbar-thumb {{ background: {KAPAK}; border-radius: 3px; }}
</style>
""", unsafe_allow_html=True)

# --- VERİ DOSYASI -------------------------------------------------------------
DATA_FILE = "SARJ.csv"

def load_data():
    if not os.path.exists(DATA_FILE):
        cols = ['TARIH','BASLANGIC SAATI','BITIS SAATI','SARJ SURESI (DK)',
                'ARAC KM','BASLANGIC YUZDESI','BITIS YUZDESI','FARK YUZDESI',
                'SARJ TIPI','SARJ FIRMASI ADI','KW UCRETI','UCRET TIPI',
                'FATURADA ALINAN KW','UCRETLI ALINAN KW','UCRETLI ALIM TUTARI',
                "ACIL OSGB'DEN ALINAN KW","ACIL OSGB'YE ODENMEYEN TUTAR",
                'HEDIYE KW','HEDIYE ALIM TUTARI','LOKALIZASYON',
                'WLTP MENZIL','PROFIL MENZIL','ACIKLAMA','GERCEK ALINAN KW']
        return pd.DataFrame(columns=cols)
    df = pd.read_csv(DATA_FILE, sep=';', encoding='utf-8-sig')
    df = df.dropna(subset=['TARIH'])
    # Sayısal çevirme (virgüllü → noktalı)
    num_cols = ['SARJ SURESI (DK)','ARAC KM','KW UCRETI',
                'UCRETLI ALINAN KW','UCRETLI ALIM TUTARI',
                "ACIL OSGB'DEN ALINAN KW","ACIL OSGB'YE ODENMEYEN TUTAR",
                'HEDIYE KW','HEDIYE ALIM TUTARI','WLTP MENZIL','PROFIL MENZIL']
    for c in num_cols:
        if c in df.columns:
            df[c] = df[c].astype(str).str.replace(',','.').str.strip()
            df[c] = pd.to_numeric(df[c], errors='coerce')
    return df

def save_row(row_dict):
    df = load_data()
    new_row = pd.DataFrame([row_dict])
    df = pd.concat([df, new_row], ignore_index=True)
    df.to_csv(DATA_FILE, sep=';', index=False, encoding='utf-8-sig')

def to_num(val, default=0.0):
    try:
        return float(str(val).replace(',','.'))
    except:
        return default

# --- HESAPLAMALAR -------------------------------------------------------------
def compute_stats(df):
    s = {}
    # kW toplamları
    s['ucretli_kw']   = df['UCRETLI ALINAN KW'].sum(skipna=True)
    s['osgb_kw']      = df["ACIL OSGB'DEN ALINAN KW"].sum(skipna=True)
    s['hediye_kw']    = df['HEDIYE KW'].sum(skipna=True)
    s['toplam_kw']    = s['ucretli_kw'] + s['osgb_kw'] + s['hediye_kw']

    # Tutar toplamları
    s['ucretli_tutar'] = df['UCRETLI ALIM TUTARI'].sum(skipna=True)
    s['osgb_tutar']    = df["ACIL OSGB'YE ODENMEYEN TUTAR"].sum(skipna=True)
    s['hediye_tutar']  = df['HEDIYE ALIM TUTARI'].sum(skipna=True)
    s['toplam_tutar']  = s['ucretli_tutar'] + s['osgb_tutar'] + s['hediye_tutar']

    # DC / AC
    dc = df[df['SARJ TIPI'] == 'DC']
    ac = df[df['SARJ TIPI'] == 'AC']
    s['dc_kw']    = dc['UCRETLI ALINAN KW'].sum(skipna=True) + dc["ACIL OSGB'DEN ALINAN KW"].sum(skipna=True) + dc['HEDIYE KW'].sum(skipna=True)
    s['ac_kw']    = ac['UCRETLI ALINAN KW'].sum(skipna=True) + ac["ACIL OSGB'DEN ALINAN KW"].sum(skipna=True) + ac['HEDIYE KW'].sum(skipna=True)
    s['dc_tutar'] = dc['UCRETLI ALIM TUTARI'].sum(skipna=True) + dc["ACIL OSGB'YE ODENMEYEN TUTAR"].sum(skipna=True) + dc['HEDIYE ALIM TUTARI'].sum(skipna=True)
    s['ac_tutar'] = ac['UCRETLI ALIM TUTARI'].sum(skipna=True) + ac["ACIL OSGB'YE ODENMEYEN TUTAR"].sum(skipna=True) + ac['HEDIYE ALIM TUTARI'].sum(skipna=True)

    # Son km
    try:
        last_km = to_num(df['ARAC KM'].dropna().iloc[-1])
    except:
        last_km = 0
    s['son_km'] = last_km

    # Ortalama km/TL
    s['ort_km_tl'] = last_km / s['toplam_tutar'] if s['toplam_tutar'] > 0 else 0

    # Süre hesaplamaları
    uc_dc = df[(df['SARJ TIPI']=='DC') & (df['UCRET TIPI'].isin(['UCRETLI','ISKONTOLU UCRETLI']))]
    uc_ac = df[(df['SARJ TIPI']=='AC') & (df['UCRET TIPI'].isin(['UCRETLI','ISKONTOLU UCRETLI']))]
    u_ac  = df[(df['SARJ TIPI']=='AC') & (df['UCRET TIPI']=='UCRETSIZ')]
    h_dc  = df[(df['SARJ TIPI']=='DC') & (df['UCRET TIPI']=='HEDIYE')]
    s['sure_ucretli_dc'] = uc_dc['SARJ SURESI (DK)'].sum(skipna=True)
    s['sure_ucretli_ac'] = uc_ac['SARJ SURESI (DK)'].sum(skipna=True)
    s['sure_ucretsiz_ac']= u_ac['SARJ SURESI (DK)'].sum(skipna=True)
    s['sure_hediye_dc']  = h_dc['SARJ SURESI (DK)'].sum(skipna=True)

    return s

# --- ANA UYGULAMA -------------------------------------------------------------
df = load_data()

# -- HEADER ---------------------------------------------------------------------
col_img, col_title = st.columns([1, 3])
with col_img:
    if os.path.exists("araba.jpeg"):
        st.image("araba.jpeg", use_container_width=True)
with col_title:
    st.markdown(f"""
    <div style="padding-top:20px">
      <div style="color:{KAPAK};font-size:13px;font-weight:600;letter-spacing:2px;">35 CTT 500 • TOGG T10X KAP ADO KYA</div>
      <h1 style="margin:4px 0;font-size:36px;font-weight:800;color:{TEXT};">⚡ ŞARJ TAKİBİ</h1>
      <div style="color:#666;font-size:13px;">Toplam {len(df)} şarj kaydı</div>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# -- SEKMELER -------------------------------------------------------------------
tab1, tab2, tab3 = st.tabs(["📊 ÖZET & GRAFİKLER", "➕ YENİ ŞARJ EKLE", "📋 TÜM VERİLER"])

# ══════════════════════════════════════════════════════════════════════════════
# SEKME 1 — ÖZET & GRAFİKLER
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    if len(df) == 0:
        st.info("Henüz veri yok. 'Yeni Şarj Ekle' sekmesinden kayıt girin.")
    else:
        stats = compute_stats(df)

        # -- KARTLAR ----------------------------------------------------------
        st.markdown("### 📦 GENEL ÖZET")
        r1 = st.columns(4)
        r1[0].metric("⚡ TOPLAM ALINAN kW",        f"{stats['toplam_kw']:,.2f} kWh")
        r1[1].metric("💰 TOPLAM TUTAR",              f"{stats['toplam_tutar']:,.2f} ₺")
        r1[2].metric("🚗 SON KM",                    f"{stats['son_km']:,.0f} km")
        r1[3].metric("📏 ORTALAMA km/₺",             f"{stats['ort_km_tl']:.2f}")

        st.markdown("")
        r2 = st.columns(4)
        r2[0].metric("💳 ÜCRETLİ kW",               f"{stats['ucretli_kw']:,.2f} kWh")
        r2[1].metric("🏥 ACİL OSGB kW",              f"{stats['osgb_kw']:,.2f} kWh")
        r2[2].metric("🎁 HEDİYE kW",                 f"{stats['hediye_kw']:,.2f} kWh")
        r2[3].metric("💳 ÜCRETLİ TUTAR",             f"{stats['ucretli_tutar']:,.2f} ₺")

        r3 = st.columns(4)
        r3[0].metric("🏥 OSGB'YE ÖDENMEYENOSGb",    f"{stats['osgb_tutar']:,.2f} ₺")
        r3[1].metric("🎁 HEDİYE TUTAR",              f"{stats['hediye_tutar']:,.2f} ₺")
        r3[2].metric("⚡ DC TOPLAM kW",               f"{stats['dc_kw']:,.2f} kWh")
        r3[3].metric("🔌 AC TOPLAM kW",               f"{stats['ac_kw']:,.2f} kWh")

        r4 = st.columns(4)
        r4[0].metric("⚡ DC TOPLAM TUTAR",            f"{stats['dc_tutar']:,.2f} ₺")
        r4[1].metric("🔌 AC TOPLAM TUTAR",            f"{stats['ac_tutar']:,.2f} ₺")
        r4[2].metric("⏱️ ÜCRETLİ DC SÜRESİ",        f"{int(stats['sure_ucretli_dc'])} dk")
        r4[3].metric("⏱️ ÜCRETLİ AC SÜRESİ",        f"{int(stats['sure_ucretli_ac'])} dk")

        r5 = st.columns(2)
        r5[0].metric("⏱️ ÜCRETSİZ AC SÜRESİ",       f"{int(stats['sure_ucretsiz_ac'])} dk")
        r5[1].metric("⏱️ HEDİYE DC SÜRESİ",         f"{int(stats['sure_hediye_dc'])} dk")

        st.divider()

        # -- GRAFİKLER --------------------------------------------------------
        st.markdown("### 📈 GRAFİKLER")

        pie_colors = [KAPAK, "#7B6B52", "#E8D5B0", "#5A4A35", "#D4B896"]

        # PASTA GRAFİKLERİ
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            labels_kw = ['ÜCRETLİ DC', 'ACİL OSGB', 'HEDİYE']
            vals_kw   = [stats['ucretli_kw'], stats['osgb_kw'], stats['hediye_kw']]
            vals_kw   = [v for v in vals_kw if v > 0]
            lbls_kw   = [l for l,v in zip(labels_kw,[stats['ucretli_kw'],stats['osgb_kw'],stats['hediye_kw']]) if v > 0]
            fig = px.pie(values=vals_kw, names=lbls_kw,
                         title='kW DAĞILIMI (TÜRE GÖRE)',
                         color_discrete_sequence=pie_colors)
            fig.update_traces(textinfo='label+value+percent', hole=0.35,
                              textfont_size=12)
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                              font_color=TEXT, title_font_color=KAPAK)
            st.plotly_chart(fig, use_container_width=True)

        with col_p2:
            labels_t = ['ÜCRETLİ', 'OSGB ÖDENMEDİ', 'HEDİYE']
            vals_t   = [stats['ucretli_tutar'], stats['osgb_tutar'], stats['hediye_tutar']]
            vals_t2  = [v for v in vals_t if v > 0]
            lbls_t2  = [l for l,v in zip(labels_t, vals_t) if v > 0]
            fig2 = px.pie(values=vals_t2, names=lbls_t2,
                          title='TUTAR DAĞILIMI (TÜRE GÖRE)',
                          color_discrete_sequence=pie_colors)
            fig2.update_traces(textinfo='label+value+percent', hole=0.35,
                               textfont_size=12)
            fig2.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                               font_color=TEXT, title_font_color=KAPAK)
            st.plotly_chart(fig2, use_container_width=True)

        # FİRMAYA GÖRE kW
        firm_kw = (
            df.assign(
                TOPLAM_KW=df['UCRETLI ALINAN KW'].fillna(0) +
                           df["ACIL OSGB'DEN ALINAN KW"].fillna(0) +
                           df['HEDIYE KW'].fillna(0)
            )
            .groupby('SARJ FIRMASI ADI')['TOPLAM_KW']
            .sum()
            .sort_values()
            .reset_index()
        )
        firm_kw.columns = ['FİRMA', 'kW']

        firm_tutar = (
            df.assign(
                TOPLAM_TUTAR=df['UCRETLI ALIM TUTARI'].fillna(0) +
                              df["ACIL OSGB'YE ODENMEYEN TUTAR"].fillna(0) +
                              df['HEDIYE ALIM TUTARI'].fillna(0)
            )
            .groupby('SARJ FIRMASI ADI')['TOPLAM_TUTAR']
            .sum()
            .sort_values()
            .reset_index()
        )
        firm_tutar.columns = ['FİRMA', 'TUTAR']

        col_b1, col_b2 = st.columns(2)
        with col_b1:
            fig3 = px.bar(firm_kw, x='kW', y='FİRMA', orientation='h',
                          title='FİRMALARA GÖRE kW',
                          text='kW',
                          color_discrete_sequence=[KAPAK])
            fig3.update_traces(texttemplate='%{text:.2f}', textposition='outside')
            fig3.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                               font_color=TEXT, title_font_color=KAPAK,
                               xaxis=dict(gridcolor='#2A2A2A'),
                               yaxis=dict(gridcolor='#2A2A2A'))
            st.plotly_chart(fig3, use_container_width=True)

        with col_b2:
            fig4 = px.bar(firm_tutar, x='TUTAR', y='FİRMA', orientation='h',
                          title='FİRMALARA GÖRE TUTAR (₺)',
                          text='TUTAR',
                          color_discrete_sequence=[KAPAK_D])
            fig4.update_traces(texttemplate='%{text:.2f} ₺', textposition='outside')
            fig4.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                               font_color=TEXT, title_font_color=KAPAK,
                               xaxis=dict(gridcolor='#2A2A2A'),
                               yaxis=dict(gridcolor='#2A2A2A'))
            st.plotly_chart(fig4, use_container_width=True)

        # AYLARA GÖRE
        df_month = df.copy()
        df_month['TARIH_DT'] = pd.to_datetime(df_month['TARIH'], dayfirst=True, errors='coerce')
        df_month['AY'] = df_month['TARIH_DT'].dt.strftime('%Y-%m')
        df_month = df_month.dropna(subset=['AY'])
        df_month['TOPLAM_KW']   = df_month['UCRETLI ALINAN KW'].fillna(0) + df_month["ACIL OSGB'DEN ALINAN KW"].fillna(0) + df_month['HEDIYE KW'].fillna(0)
        df_month['TOPLAM_TUTAR']= df_month['UCRETLI ALIM TUTARI'].fillna(0) + df_month["ACIL OSGB'YE ODENMEYEN TUTAR"].fillna(0) + df_month['HEDIYE ALIM TUTARI'].fillna(0)

        ay_kw    = df_month.groupby('AY')['TOPLAM_KW'].sum().reset_index().sort_values('AY')
        ay_tutar = df_month.groupby('AY')['TOPLAM_TUTAR'].sum().reset_index().sort_values('AY')

        col_m1, col_m2 = st.columns(2)
        with col_m1:
            fig5 = px.bar(ay_kw, x='TOPLAM_KW', y='AY', orientation='h',
                          title='AYLARA GÖRE kWh',
                          text='TOPLAM_KW',
                          color_discrete_sequence=[KAPAK])
            fig5.update_traces(texttemplate='%{text:.2f}', textposition='outside')
            fig5.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                               font_color=TEXT, title_font_color=KAPAK,
                               xaxis=dict(gridcolor='#2A2A2A'),
                               yaxis=dict(gridcolor='#2A2A2A'))
            st.plotly_chart(fig5, use_container_width=True)

        with col_m2:
            fig6 = px.bar(ay_tutar, x='TOPLAM_TUTAR', y='AY', orientation='h',
                          title='AYLARA GÖRE TUTAR (₺)',
                          text='TOPLAM_TUTAR',
                          color_discrete_sequence=[KAPAK_D])
            fig6.update_traces(texttemplate='%{text:.2f} ₺', textposition='outside')
            fig6.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                               font_color=TEXT, title_font_color=KAPAK,
                               xaxis=dict(gridcolor='#2A2A2A'),
                               yaxis=dict(gridcolor='#2A2A2A'))
            st.plotly_chart(fig6, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# SEKME 2 — YENİ ŞARJ EKLE
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown("### ➕ YENİ ŞARJ KAYDI EKLE")

    with st.form("sarj_form", clear_on_submit=True):
        # -- SATIR 1: TARİH & SAATLER --------------------------------------
        c1, c2, c3 = st.columns(3)
        with c1:
            tarih = st.date_input("📅 TARİH", value=datetime.today(),
                                  format="DD/MM/YYYY")
        with c2:
            bas_saat = st.time_input("🕐 BAŞLANGIÇ SAATİ", value=time(8, 0), step=60)
        with c3:
            bit_saat = st.time_input("🕑 BİTİŞ SAATİ", value=time(9, 0), step=60)

        # Süre otomatik
        bas_dt = datetime.combine(tarih, bas_saat)
        bit_dt = datetime.combine(tarih, bit_saat)
        if bit_dt < bas_dt:
            from datetime import timedelta
            bit_dt += timedelta(days=1)
        sure_dk = int((bit_dt - bas_dt).total_seconds() / 60)
        st.info(f"⏱️ **TOPLAM ŞARJ SÜRESİ:** {sure_dk} dakika")

        # -- SATIR 2: KM & ENERJI ------------------------------------------
        c4, c5 = st.columns(2)
        with c4:
            arac_km = st.number_input("🚗 ARAÇ KM'Sİ", min_value=0.0, step=1.0, format="%.0f")
        with c5:
            st.markdown("**⚡ ENERJİ YÜZDELERİ**")
            bas_yuzde = st.slider("BAŞLANGIÇ ENERJİ (%)", 0, 100, 50,
                                  key="bas_yuzde")
            bit_yuzde = st.slider("BİTİŞ ENERJİ (%)", 0, 100, 80,
                                  key="bit_yuzde")
            fark_yuzde = bit_yuzde - bas_yuzde
            st.markdown(f"**FARK: %{fark_yuzde}**")

        # Gerçek kW (fark_yuzde * 0.885)
        gercek_kw = fark_yuzde * 0.885

        # -- SATIR 3: ŞARJ TİPİ & FİRMA -----------------------------------
        c6, c7, c8 = st.columns(3)
        with c6:
            sarj_tipi = st.selectbox("⚡ ŞARJ TİPİ",
                                     ['DC', 'AC', 'ACİL OSGB', 'HEDİYE'])
        with c7:
            sarj_firma = st.text_input("🏢 ŞARJ FİRMASI ADI",
                                       placeholder="ZES, EŞARJ, WAT...").upper()
        with c8:
            kw_ucreti = st.number_input("💲 kW ÜCRETİ (₺/kWh)",
                                        min_value=0.0, step=0.01, format="%.2f")

        c9, c10 = st.columns(2)
        with c9:
            ucret_tipi = st.selectbox("💳 ÜCRET TİPİ",
                                      ['ÜCRETLİ', 'ÜCRETSİZ', 'İSKONTOLU ÜCRETLİ', 'HEDİYE'])
        with c10:
            faturada_kw = st.number_input("📄 FATURADA ALINAN kW",
                                          min_value=0.0, step=0.01, format="%.2f")

        # -- SATIR 4: KW & TUTARLAR ----------------------------------------
        c11, c12, c13 = st.columns(3)
        with c11:
            ucretli_kw = st.number_input("⚡ ÜCRETLİ ALINAN kW",
                                         min_value=0.0, step=0.01, format="%.2f")
        with c12:
            ucretli_tutar = st.number_input("💰 ÜCRETLİ ALIM TUTARI (₺)",
                                            min_value=0.0, step=0.01, format="%.2f")
        with c13:
            osgb_kw = st.number_input("🏥 ACİL OSGB'DEN ALINAN kW",
                                      min_value=0.0, step=0.01, format="%.2f")

        c14, c15, c16 = st.columns(3)
        with c14:
            osgb_tutar = st.number_input("🏥 OSGB'YE ÖDENMEYENOSGb TUTAR (₺)",
                                         min_value=0.0, step=0.01, format="%.2f")
        with c15:
            hediye_kw = st.number_input("🎁 HEDİYE ALINAN kW",
                                        min_value=0.0, step=0.01, format="%.2f")
        with c16:
            hediye_tutar = st.number_input("🎁 HEDİYE ALIM TUTARI (₺)",
                                           min_value=0.0, step=0.01, format="%.2f")

        # -- SATIR 5: MENZİL & LOKALİZASYON ------------------------------
        c17, c18, c19 = st.columns(3)
        with c17:
            lokalizasyon = st.text_input("📍 LOKALİZASYON",
                                         placeholder="İZMİR...").upper()
        with c18:
            wltp = st.number_input("🛣️ WLTP MENZİL (km)",
                                   min_value=0.0, step=1.0, format="%.0f")
        with c19:
            profil = st.number_input("📊 PROFİL MENZİL (km)",
                                     min_value=0.0, step=1.0, format="%.0f")

        # -- AÇIKLAMA ------------------------------------------------------
        aciklama = st.text_area("📝 AÇIKLAMA", height=100,
                                placeholder="İsteğe bağlı açıklama...").upper()

        # -- GERÇEK kW GÖSTER ----------------------------------------------
        st.markdown(f"""
        <div style="background:{CARD2_BG};border:1px solid {KAPAK};border-radius:10px;
                    padding:12px 20px;margin:12px 0;">
          <span style="color:{KAPAK};font-weight:700;">⚙️ GERÇEK ALINAN kW:</span>
          <span style="font-size:20px;font-weight:800;margin-left:12px;">
            {gercek_kw:.2f} kWh
          </span>
          <span style="color:#666;font-size:12px;margin-left:8px;">
            (%{fark_yuzde} × 0,885)
          </span>
        </div>
        """, unsafe_allow_html=True)

        # -- KAYDET BUTONU -------------------------------------------------
        st.markdown("<br>", unsafe_allow_html=True)
        col_save1, col_save2, col_save3 = st.columns([1, 2, 1])
        with col_save2:
            submitted = st.form_submit_button(
                "💾  KAYDET",
                use_container_width=True
            )

        if submitted:
            ucret_map = {
                'ÜCRETLİ': 'UCRETLI',
                'ÜCRETSİZ': 'UCRETSIZ',
                'İSKONTOLU ÜCRETLİ': 'ISKONTOLU UCRETLI',
                'HEDİYE': 'HEDIYE'
            }
            sarj_map = {
                'ACİL OSGB': 'AC',
                'HEDİYE': 'DC',
            }
            row = {
                'TARIH': tarih.strftime('%d.%m.%Y'),
                'BASLANGIC SAATI': bas_saat.strftime('%H:%M:%S'),
                'BITIS SAATI': bit_saat.strftime('%H:%M:%S'),
                'SARJ SURESI (DK)': sure_dk,
                'ARAC KM': arac_km,
                'BASLANGIC YUZDESI': f'%{bas_yuzde}',
                'BITIS YUZDESI': f'%{bit_yuzde}',
                'SARJ TIPI': sarj_map.get(sarj_tipi, sarj_tipi),
                'SARJ FIRMASI ADI': sarj_firma,
                'KW UCRETI': str(kw_ucreti).replace('.',','),
                'UCRET TIPI': ucret_map.get(ucret_tipi, ucret_tipi),
                'UCRETLI ALINAN KW': ucretli_kw if ucretli_kw > 0 else None,
                'UCRETLI ALIM TUTARI': ucretli_tutar if ucretli_tutar > 0 else None,
                "ACIL OSGB'DEN ALINAN KW": osgb_kw if osgb_kw > 0 else None,
                "ACIL OSGB'YE ODENMEYEN TUTAR": osgb_tutar if osgb_tutar > 0 else None,
                'HEDIYE KW': hediye_kw if hediye_kw > 0 else None,
                'HEDIYE ALIM TUTARI': hediye_tutar if hediye_tutar > 0 else None,
                'LOKALIZASYON': lokalizasyon,
                'WLTP MENZIL': wltp if wltp > 0 else None,
                'PROFIL MENZIL': profil if profil > 0 else None,
                'ACIKLAMA': aciklama,
                'GERCEK ALINAN KW': round(gercek_kw, 4),
            }
            save_row(row)
            st.success(f"✅ Kayıt başarıyla eklendi! ({tarih.strftime('%d.%m.%Y')} — {sarj_firma})")
            st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# SEKME 3 — TÜM VERİLER
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown("### 📋 TÜM ŞARJ KAYITLARI")
    if len(df) == 0:
        st.info("Henüz kayıt yok.")
    else:
        show_cols = ['TARIH','BASLANGIC SAATI','BITIS SAATI','SARJ SURESI (DK)',
                     'ARAC KM','BASLANGIC YUZDESI','BITIS YUZDESI',
                     'SARJ TIPI','SARJ FIRMASI ADI','UCRET TIPI',
                     'UCRETLI ALINAN KW','UCRETLI ALIM TUTARI',
                     "ACIL OSGB'DEN ALINAN KW","ACIL OSGB'YE ODENMEYEN TUTAR",
                     'HEDIYE KW','HEDIYE ALIM TUTARI','LOKALIZASYON','ACIKLAMA']
        existing = [c for c in show_cols if c in df.columns]
        st.dataframe(
            df[existing].reset_index(drop=True),
            use_container_width=True,
            height=600
        )
        # İndirme butonu
        csv_bytes = df.to_csv(sep=';', index=False, encoding='utf-8-sig').encode('utf-8-sig')
        st.download_button(
            label="⬇️ CSV OLARAK İNDİR",
            data=csv_bytes,
            file_name="SARJ_VERILERI.csv",
            mime="text/csv"
        )
