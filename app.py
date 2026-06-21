import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, time, timedelta
import os

# ============================================================
# SAYFA AYARLARI
# ============================================================
st.set_page_config(
    page_title="TOGG SARJ TAKİBİ",
    page_icon="⚡",
    layout="centered",
    initial_sidebar_state="collapsed"
)

KAPAK   = "#C4A882"
KAPAK_D = "#A08060"
DARK_BG = "#0F0F0F"
CARD_BG = "#1A1A1A"
CARD2   = "#242424"
TEXT    = "#F5F0EA"

st.markdown(f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');

  html, body, [class*="css"] {{
    font-family: 'Inter', sans-serif !important;
    background-color: {DARK_BG} !important;
    color: {TEXT} !important;
  }}
  .stApp {{ background-color: {DARK_BG} !important; }}

  .block-container {{
    padding: 0.5rem 0.8rem 2rem 0.8rem !important;
    max-width: 520px !important;
  }}

  [data-testid="stSidebar"] {{ display: none !important; }}

  .stTabs [data-baseweb="tab-list"] {{
    gap: 3px;
    background: {CARD_BG};
    border-radius: 14px;
    padding: 4px;
    margin-bottom: 8px;
  }}
  .stTabs [data-baseweb="tab"] {{
    background: transparent !important;
    color: #888 !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    font-size: 11px !important;
    padding: 8px 4px !important;
    min-height: 40px !important;
  }}
  .stTabs [aria-selected="true"] {{
    background: {KAPAK} !important;
    color: #000 !important;
  }}

  [data-testid="metric-container"] {{
    background: {CARD_BG} !important;
    border: 1px solid #2A2A2A !important;
    border-radius: 14px !important;
    padding: 10px 14px !important;
    margin-bottom: 4px !important;
  }}
  [data-testid="stMetricLabel"] {{
    font-size: 10px !important;
    color: #888 !important;
    font-weight: 600 !important;
    letter-spacing: 0.5px !important;
    text-transform: uppercase !important;
  }}
  [data-testid="stMetricValue"] {{
    font-size: 18px !important;
    font-weight: 800 !important;
    color: {KAPAK} !important;
  }}

  .stTextInput input,
  .stNumberInput input,
  .stTimeInput input {{
    background-color: {CARD2} !important;
    color: {TEXT} !important;
    border: 1px solid #333 !important;
    border-radius: 10px !important;
    font-size: 16px !important;
    padding: 10px 12px !important;
    min-height: 48px !important;
  }}
  .stSelectbox > div > div {{
    background-color: {CARD2} !important;
    color: {TEXT} !important;
    border: 1px solid #333 !important;
    border-radius: 10px !important;
    min-height: 48px !important;
    font-size: 16px !important;
  }}
  .stTextArea textarea {{
    background-color: {CARD2} !important;
    color: {TEXT} !important;
    border: 1px solid #333 !important;
    border-radius: 10px !important;
    font-size: 15px !important;
  }}

  .stTextInput label, .stNumberInput label,
  .stSelectbox label, .stSlider label,
  .stTimeInput label, .stDateInput label,
  .stTextArea label {{
    color: {TEXT} !important;
    font-size: 12px !important;
    font-weight: 700 !important;
    letter-spacing: 0.5px !important;
    text-transform: uppercase !important;
    margin-bottom: 4px !important;
  }}

  .stSlider [data-baseweb="slider"] div[role="slider"] {{
    background-color: {KAPAK} !important;
    width: 24px !important;
    height: 24px !important;
  }}

  .stButton > button, .stFormSubmitButton > button {{
    background-color: {KAPAK} !important;
    color: #000 !important;
    font-weight: 800 !important;
    border: none !important;
    border-radius: 14px !important;
    padding: 14px 20px !important;
    font-size: 16px !important;
    min-height: 52px !important;
    width: 100% !important;
    letter-spacing: 0.5px !important;
  }}
  .stDownloadButton > button {{
    background-color: {CARD2} !important;
    color: {KAPAK} !important;
    border: 1px solid {KAPAK} !important;
    border-radius: 14px !important;
    font-weight: 700 !important;
    font-size: 14px !important;
    min-height: 48px !important;
    width: 100% !important;
  }}

  hr {{ border-color: #2A2A2A !important; margin: 8px 0 !important; }}

  h1 {{ font-size: 24px !important; color: {TEXT} !important; margin: 0 !important; }}
  h2 {{ font-size: 18px !important; color: {TEXT} !important; margin: 8px 0 4px 0 !important; }}
  h3 {{ font-size: 15px !important; color: {KAPAK} !important;
        letter-spacing: 1px !important; margin: 12px 0 6px 0 !important; }}

  .stAlert {{
    border-radius: 12px !important;
    font-size: 14px !important;
  }}

  .stDataFrame {{
    border-radius: 12px !important;
    overflow: hidden !important;
    font-size: 12px !important;
  }}

  ::-webkit-scrollbar {{ width: 4px; }}
  ::-webkit-scrollbar-thumb {{ background: {KAPAK}; border-radius: 2px; }}

  .stDateInput input {{
    background-color: {CARD2} !important;
    color: {TEXT} !important;
    border: 1px solid #333 !important;
    border-radius: 10px !important;
    font-size: 16px !important;
    min-height: 48px !important;
  }}

  .js-plotly-plot {{ border-radius: 12px !important; }}
</style>
""", unsafe_allow_html=True)

# ============================================================
# VERİ
# ============================================================
DATA_FILE = "SARJ.csv"

def load_data():
    if not os.path.exists(DATA_FILE):
        return pd.DataFrame(columns=[
            'TARIH','BASLANGIC SAATI','BITIS SAATI','SARJ SURESI (DK)',
            'ARAC KM','BASLANGIC YUZDESI','BITIS YUZDESI',
            'SARJ TIPI','SARJ FIRMASI ADI','KW UCRETI','UCRET TIPI',
            'UCRETLI ALINAN KW','UCRETLI ALIM TUTARI',
            "ACIL OSGB'DEN ALINAN KW","ACIL OSGB'YE ODENMEYEN TUTAR",
            'HEDIYE KW','HEDIYE ALIM TUTARI','LOKALIZASYON',
            'WLTP MENZIL','PROFIL MENZIL','ACIKLAMA','GERCEK ALINAN KW'
        ])
    df = pd.read_csv(DATA_FILE, sep=';', encoding='utf-8-sig')
    df = df.dropna(subset=['TARIH'])
    num_cols = [
        'SARJ SURESI (DK)','ARAC KM','KW UCRETI',
        'UCRETLI ALINAN KW','UCRETLI ALIM TUTARI',
        "ACIL OSGB'DEN ALINAN KW","ACIL OSGB'YE ODENMEYEN TUTAR",
        'HEDIYE KW','HEDIYE ALIM TUTARI','WLTP MENZIL','PROFIL MENZIL'
    ]
    for c in num_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(
                df[c].astype(str).str.strip()
                     .str.replace(r'\.(?=\d{3}(?:[,.]|\s*$))', '', regex=True)
                     .str.replace(',', '.', regex=False),
                errors='coerce'
            )
    return df

def save_row(row_dict):
    df = load_data()
    df = pd.concat([df, pd.DataFrame([row_dict])], ignore_index=True)
    df.to_csv(DATA_FILE, sep=';', index=False, encoding='utf-8-sig')

def to_num(val, default=0.0):
    try:
        import re
        s = str(val).strip()
        s = re.sub(r'\.(?=\d{3}(?:[,.]|\s*$))', '', s)
        s = s.replace(',', '.')
        return float(s)
    except Exception:
        return default

def compute_stats(df):
    s = {}
    s['ucretli_kw']    = df['UCRETLI ALINAN KW'].sum(skipna=True)
    s['osgb_kw']       = df["ACIL OSGB'DEN ALINAN KW"].sum(skipna=True)
    s['hediye_kw']     = df['HEDIYE KW'].sum(skipna=True)
    s['toplam_kw']     = s['ucretli_kw'] + s['osgb_kw'] + s['hediye_kw']
    s['ucretli_tutar'] = df['UCRETLI ALIM TUTARI'].sum(skipna=True)
    s['osgb_tutar']    = df["ACIL OSGB'YE ODENMEYEN TUTAR"].sum(skipna=True)
    s['hediye_tutar']  = df['HEDIYE ALIM TUTARI'].sum(skipna=True)
    s['toplam_tutar']  = s['ucretli_tutar'] + s['osgb_tutar'] + s['hediye_tutar']
    dc = df[df['SARJ TIPI'] == 'DC']
    ac = df[df['SARJ TIPI'] == 'AC']
    def kw_sum(sub):
        return (sub['UCRETLI ALINAN KW'].sum(skipna=True)
                + sub["ACIL OSGB'DEN ALINAN KW"].sum(skipna=True)
                + sub['HEDIYE KW'].sum(skipna=True))
    def t_sum(sub):
        return (sub['UCRETLI ALIM TUTARI'].sum(skipna=True)
                + sub["ACIL OSGB'YE ODENMEYEN TUTAR"].sum(skipna=True)
                + sub['HEDIYE ALIM TUTARI'].sum(skipna=True))
    s['dc_kw']    = kw_sum(dc)
    s['ac_kw']    = kw_sum(ac)
    s['dc_tutar'] = t_sum(dc)
    s['ac_tutar'] = t_sum(ac)
    try:
        s['son_km'] = float(df['ARAC KM'].dropna().iloc[-1])
    except Exception:
        s['son_km'] = 0
    s['ort_km_tl'] = s['son_km'] / s['toplam_tutar'] if s['toplam_tutar'] > 0 else 0
    uc_dc = df[(df['SARJ TIPI'] == 'DC') & (df['UCRET TIPI'].isin(['UCRETLI', 'ISKONTOLU UCRETLI']))]
    uc_ac = df[(df['SARJ TIPI'] == 'AC') & (df['UCRET TIPI'].isin(['UCRETLI', 'ISKONTOLU UCRETLI']))]
    u_ac  = df[(df['SARJ TIPI'] == 'AC') & (df['UCRET TIPI'] == 'UCRETSIZ')]
    h_dc  = df[(df['SARJ TIPI'] == 'DC') & (df['UCRET TIPI'] == 'HEDIYE')]
    s['sure_ucretli_dc']  = uc_dc['SARJ SURESI (DK)'].sum(skipna=True)
    s['sure_ucretli_ac']  = uc_ac['SARJ SURESI (DK)'].sum(skipna=True)
    s['sure_ucretsiz_ac'] = u_ac['SARJ SURESI (DK)'].sum(skipna=True)
    s['sure_hediye_dc']   = h_dc['SARJ SURESI (DK)'].sum(skipna=True)
    return s

# ============================================================
# VERİYİ YÜKLE
# ============================================================
df = load_data()

# ============================================================
# HEADER — araba görseli + başlık
# ============================================================
if os.path.exists("araba.jpeg"):
    st.image("araba.jpeg", use_container_width=True)

st.markdown(f"""
<div style="display:flex;align-items:center;gap:12px;padding:8px 0 12px 0;
            border-bottom:1px solid #2A2A2A;margin-bottom:12px;">
  <div style="font-size:36px;">⚡</div>
  <div>
    <div style="font-size:10px;color:{KAPAK};font-weight:700;letter-spacing:2px;">
      35 CTT 500 &bull; TOGG T10X KAPADOKYA
    </div>
    <div style="font-size:22px;font-weight:800;color:{TEXT};line-height:1.2;">
      SARJ TAKİBİ
    </div>
    <div style="font-size:11px;color:#555;">{len(df)} kayıt</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ============================================================
# SEKMELER
# ============================================================
tab1, tab2, tab3 = st.tabs(["📊 ÖZET", "➕ YENİ KAYIT", "📋 VERİLER"])

# ===========================================================
# TAB 1 — ÖZET
# ===========================================================
with tab1:
    if len(df) == 0:
        st.info("Henüz veri yok.")
    else:
        stats = compute_stats(df)

        def kart(label, value, icon="", accent=KAPAK):
            return f"""
            <div style="background:{CARD_BG};border:1px solid #2A2A2A;border-radius:16px;
                        padding:14px 16px;margin-bottom:8px;
                        border-left:3px solid {accent};">
              <div style="font-size:10px;color:#888;font-weight:700;letter-spacing:1px;
                          text-transform:uppercase;margin-bottom:6px;">{icon} {label}</div>
              <div style="font-size:22px;font-weight:800;color:{accent};line-height:1.1;">{value}</div>
            </div>"""

        def kart_row(items):
            cols_html = "".join(
                f'<div style="flex:1;min-width:0;">{kart(l, v, i, a)}</div>'
                for l, v, i, a in items
            )
            st.markdown(
                f'<div style="display:flex;gap:8px;margin-bottom:0px;">{cols_html}</div>',
                unsafe_allow_html=True
            )

        st.markdown("### ⚡ GENEL")
        kart_row([
            ("TOPLAM kW",    f"{stats['toplam_kw']:,.2f}",        "⚡", KAPAK),
            ("TOPLAM TUTAR", f"{stats['toplam_tutar']:,.2f} ₺",   "💰", KAPAK_D),
        ])
        kart_row([
            ("SON KM",  f"{stats['son_km']:,.0f} km",   "🚗", KAPAK),
            ("km / ₺",  f"{stats['ort_km_tl']:,.3f}",   "📊", KAPAK_D),
        ])

        st.markdown("### 💳 kW DAĞILIMI")
        kart_row([
            ("ÜCRETLİ kW", f"{stats['ucretli_kw']:,.2f}", "💳", KAPAK),
            ("OSGB kW",     f"{stats['osgb_kw']:,.2f}",    "🏥", KAPAK_D),
        ])
        kart_row([
            ("HEDİYE kW", f"{stats['hediye_kw']:,.2f}", "🎁", KAPAK),
            ("DC kW",      f"{stats['dc_kw']:,.2f}",      "⚡", KAPAK_D),
        ])
        kart_row([
            ("AC kW", f"{stats['ac_kw']:,.2f}", "🔌", KAPAK),
        ])

        st.markdown("### 💰 TUTAR DAĞILIMI")
        kart_row([
            ("ÜCRETLİ ₺",    f"{stats['ucretli_tutar']:,.2f} ₺", "💳", KAPAK),
            ("OSGB ÖD.YOK ₺", f"{stats['osgb_tutar']:,.2f} ₺",   "🏥", KAPAK_D),
        ])
        kart_row([
            ("HEDİYE ₺",  f"{stats['hediye_tutar']:,.2f} ₺", "🎁", KAPAK),
            ("DC TUTAR ₺", f"{stats['dc_tutar']:,.2f} ₺",     "⚡", KAPAK_D),
        ])
        kart_row([
            ("AC TUTAR ₺", f"{stats['ac_tutar']:,.2f} ₺", "🔌", KAPAK),
        ])

        st.markdown("### ⏱️ SARJ SÜRELERİ")
        kart_row([
            ("ÜC. DC (dk)",  f"{int(stats['sure_ucretli_dc']):,}",  "⚡", KAPAK),
            ("ÜC. AC (dk)",  f"{int(stats['sure_ucretli_ac']):,}",  "🔌", KAPAK_D),
        ])
        kart_row([
            ("ÜCRETSİZ AC", f"{int(stats['sure_ucretsiz_ac']):,} dk", "🆓", KAPAK),
            ("HEDİYE DC",   f"{int(stats['sure_hediye_dc']):,} dk",   "🎁", KAPAK_D),
        ])

        st.divider()

        # ---- GRAFİKLER ----
        PIE_COLORS = [KAPAK, "#7B6B52", "#E8D5B0", "#5A4A35"]
        CHART_LAYOUT = dict(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font_color=TEXT,
            title_font_color=KAPAK,
            title_font_size=13,
            margin=dict(l=0, r=80, t=36, b=0),
        )
        BAR_LAYOUT = dict(
            **CHART_LAYOUT,
            xaxis=dict(gridcolor='#2A2A2A', tickfont_size=10),
            yaxis=dict(tickfont_size=10),
        )

        st.markdown("### 🥧 kWh PASTA")
        lkw = ['ÜCRETLİ', 'OSGB', 'HEDİYE']
        vkw = [stats['ucretli_kw'], stats['osgb_kw'], stats['hediye_kw']]
        lkw2 = [l for l, v in zip(lkw, vkw) if v > 0]
        vkw2 = [v for v in vkw if v > 0]
        fig_p1 = px.pie(values=vkw2, names=lkw2,
                        color_discrete_sequence=PIE_COLORS, hole=0.4)
        fig_p1.update_traces(
            texttemplate='%{label}<br>%{value:,.2f}',
            textfont_size=11
        )
        fig_p1.update_layout(**CHART_LAYOUT)
        st.plotly_chart(fig_p1, use_container_width=True)

        st.markdown("### 🥧 TUTAR PASTA")
        lt = ['ÜCRETLİ', 'OSGB', 'HEDİYE']
        vt = [stats['ucretli_tutar'], stats['osgb_tutar'], stats['hediye_tutar']]
        lt2 = [l for l, v in zip(lt, vt) if v > 0]
        vt2 = [v for v in vt if v > 0]
        fig_p2 = px.pie(values=vt2, names=lt2,
                        color_discrete_sequence=PIE_COLORS, hole=0.4)
        fig_p2.update_traces(
            texttemplate='%{label}<br>%{value:,.2f} ₺',
            textfont_size=11
        )
        fig_p2.update_layout(**CHART_LAYOUT)
        st.plotly_chart(fig_p2, use_container_width=True)

        st.markdown("### 🏢 FİRMAYA GÖRE kWh")
        df2 = df.copy()
        df2['TOPLAM_KW'] = (df2['UCRETLI ALINAN KW'].fillna(0)
                            + df2["ACIL OSGB'DEN ALINAN KW"].fillna(0)
                            + df2['HEDIYE KW'].fillna(0))
        fkw = (df2.groupby('SARJ FIRMASI ADI')['TOPLAM_KW']
               .sum().sort_values().reset_index())
        fkw.columns = ['FİRMA', 'kWh']
        fig_b1 = px.bar(fkw, x='kWh', y='FİRMA', orientation='h',
                        text='kWh', color_discrete_sequence=[KAPAK])
        fig_b1.update_traces(
            texttemplate='%{text:,.1f}',
            textposition='outside',
            cliponaxis=False,
            textfont_size=10
        )
        fig_b1.update_layout(**BAR_LAYOUT)
        st.plotly_chart(fig_b1, use_container_width=True)

        st.markdown("### 🏢 FİRMAYA GÖRE TUTAR (₺)")
        df2['TOPLAM_TUTAR'] = (df2['UCRETLI ALIM TUTARI'].fillna(0)
                               + df2["ACIL OSGB'YE ODENMEYEN TUTAR"].fillna(0)
                               + df2['HEDIYE ALIM TUTARI'].fillna(0))
        ft = (df2.groupby('SARJ FIRMASI ADI')['TOPLAM_TUTAR']
              .sum().sort_values().reset_index())
        ft.columns = ['FİRMA', '₺']
        fig_b2 = px.bar(ft, x='₺', y='FİRMA', orientation='h',
                        text='₺', color_discrete_sequence=[KAPAK_D])
        fig_b2.update_traces(
            texttemplate='%{text:,.0f} ₺',
            textposition='outside',
            cliponaxis=False,
            textfont_size=10
        )
        fig_b2.update_layout(**BAR_LAYOUT)
        st.plotly_chart(fig_b2, use_container_width=True)

        st.markdown("### 📅 AYLARA GÖRE kWh")
        df2['TARIH_DT'] = pd.to_datetime(df2['TARIH'], dayfirst=True, errors='coerce')
        df2['AY'] = df2['TARIH_DT'].dt.strftime('%Y-%m')
        aykw = (df2.dropna(subset=['AY'])
                .groupby('AY')['TOPLAM_KW'].sum()
                .sort_index().reset_index())
        aykw.columns = ['AY', 'kWh']
        fig_m1 = px.bar(aykw, x='kWh', y='AY', orientation='h',
                        text='kWh', color_discrete_sequence=[KAPAK])
        fig_m1.update_traces(
            texttemplate='%{text:,.1f}',
            textposition='outside',
            cliponaxis=False,
            textfont_size=10
        )
        fig_m1.update_layout(**BAR_LAYOUT)
        st.plotly_chart(fig_m1, use_container_width=True)

        st.markdown("### 📅 AYLARA GÖRE TUTAR (₺)")
        ayt = (df2.dropna(subset=['AY'])
               .groupby('AY')['TOPLAM_TUTAR'].sum()
               .sort_index().reset_index())
        ayt.columns = ['AY', '₺']
        fig_m2 = px.bar(ayt, x='₺', y='AY', orientation='h',
                        text='₺', color_discrete_sequence=[KAPAK_D])
        fig_m2.update_traces(
            texttemplate='%{text:,.0f} ₺',
            textposition='outside',
            cliponaxis=False,
            textfont_size=10
        )
        fig_m2.update_layout(**BAR_LAYOUT)
        st.plotly_chart(fig_m2, use_container_width=True)

# ===========================================================
# TAB 2 — YENİ KAYIT
# ===========================================================
with tab2:
    st.markdown("### ➕ YENİ SARJ KAYDI")

    with st.form("sarj_form", clear_on_submit=True):

        tarih = st.date_input("📅 TARİH", value=datetime.today(), format="DD/MM/YYYY")

        c1, c2 = st.columns(2)
        with c1:
            bas_saat = st.time_input("🕐 BAŞLANGIÇ", value=time(8, 0), step=60)
        with c2:
            bit_saat = st.time_input("🕑 BİTİŞ", value=time(9, 0), step=60)

        bas_dt = datetime.combine(tarih, bas_saat)
        bit_dt = datetime.combine(tarih, bit_saat)
        if bit_dt < bas_dt:
            bit_dt += timedelta(days=1)
        sure_dk = int((bit_dt - bas_dt).total_seconds() / 60)

        st.markdown(f"""
        <div style="background:{CARD2};border-left:3px solid {KAPAK};
                    border-radius:8px;padding:10px 14px;margin:4px 0 12px 0;
                    font-size:14px;font-weight:700;color:{KAPAK};">
          ⏱️ SARJ SÜRESİ: {sure_dk} DAKİKA
        </div>
        """, unsafe_allow_html=True)

        st.divider()

        arac_km = st.number_input("🚗 ARAÇ KM'Sİ", min_value=0.0, step=1.0, format="%.0f")

        st.divider()

        st.markdown("**⚡ ENERJİ YÜZDELERİ**")
        bas_yuzde = st.slider("BAŞLANGIÇ (%)", 0, 100, 50, key="bas_y")
        bit_yuzde = st.slider("BİTİŞ (%)", 0, 100, 80, key="bit_y")
        fark_yuzde = bit_yuzde - bas_yuzde
        gercek_kw  = fark_yuzde * 0.885

        c1, c2, c3 = st.columns(3)
        c1.metric("BAŞLANGIÇ", f"%{bas_yuzde}")
        c2.metric("BİTİŞ", f"%{bit_yuzde}")
        c3.metric("FARK", f"%{fark_yuzde}")

        st.divider()

        sarj_tipi = st.selectbox("⚡ SARJ TİPİ", ['DC', 'AC', 'ACİL OSGB', 'HEDİYE'])
        sarj_firma = st.text_input("🏢 SARJ FİRMASI", placeholder="ZES, WAT, TRUGO...").upper()

        c1, c2 = st.columns(2)
        with c1:
            kw_ucreti = st.number_input("💲 kW ÜCRETİ (₺)", min_value=0.0, step=0.01, format="%.2f")
        with c2:
            ucret_tipi = st.selectbox("💳 ÜCRET TİPİ",
                                      ['ÜCRETLİ', 'ÜCRETSİZ', 'İSKONTOLU ÜCRETLİ', 'HEDİYE'])

        st.divider()

        faturada_kw = st.number_input("📄 FATURADA ALINAN kW", min_value=0.0, step=0.01, format="%.2f")

        c1, c2 = st.columns(2)
        with c1:
            ucretli_kw = st.number_input("⚡ ÜCRETLİ kW", min_value=0.0, step=0.01, format="%.2f")
        with c2:
            ucretli_tutar = st.number_input("💰 ÜCRETLİ ₺", min_value=0.0, step=0.01, format="%.2f")

        c1, c2 = st.columns(2)
        with c1:
            osgb_kw = st.number_input("🏥 OSGB kW", min_value=0.0, step=0.01, format="%.2f")
        with c2:
            osgb_tutar = st.number_input("🏥 OSGB ₺", min_value=0.0, step=0.01, format="%.2f")

        c1, c2 = st.columns(2)
        with c1:
            hediye_kw = st.number_input("🎁 HEDİYE kW", min_value=0.0, step=0.01, format="%.2f")
        with c2:
            hediye_tutar = st.number_input("🎁 HEDİYE ₺", min_value=0.0, step=0.01, format="%.2f")

        st.divider()

        lokalizasyon = st.text_input("📍 LOKALİZASYON", placeholder="İZMİR, NOVADA...").upper()

        c1, c2 = st.columns(2)
        with c1:
            wltp   = st.number_input("WLTP km", min_value=0.0, step=1.0, format="%.0f")
        with c2:
            profil = st.number_input("PROFİL km", min_value=0.0, step=1.0, format="%.0f")

        st.divider()

        aciklama = st.text_area("📝 AÇIKLAMA", height=90,
                                placeholder="İsteğe bağlı not...").upper()

        st.markdown(f"""
        <div style="background:{CARD2};border:1px solid {KAPAK};border-radius:12px;
                    padding:14px 16px;margin:12px 0;text-align:center;">
          <div style="font-size:11px;color:#888;font-weight:700;letter-spacing:1px;">
            GERÇEK ALINAN kW  (%{fark_yuzde} x 0.885)
          </div>
          <div style="font-size:28px;font-weight:800;color:{KAPAK};margin-top:4px;">
            {gercek_kw:,.2f} kWh
          </div>
        </div>
        """, unsafe_allow_html=True)

        submitted = st.form_submit_button("💾  KAYDET", use_container_width=True)

        if submitted:
            ucret_map = {
                'ÜCRETLİ': 'UCRETLI',
                'ÜCRETSİZ': 'UCRETSIZ',
                'İSKONTOLU ÜCRETLİ': 'ISKONTOLU UCRETLI',
                'HEDİYE': 'HEDIYE'
            }
            sarj_map = {'ACİL OSGB': 'AC', 'HEDİYE': 'DC'}
            row = {
                'TARIH':               tarih.strftime('%d.%m.%Y'),
                'BASLANGIC SAATI':     bas_saat.strftime('%H:%M:%S'),
                'BITIS SAATI':         bit_saat.strftime('%H:%M:%S'),
                'SARJ SURESI (DK)':    sure_dk,
                'ARAC KM':             arac_km,
                'BASLANGIC YUZDESI':   f'%{bas_yuzde}',
                'BITIS YUZDESI':       f'%{bit_yuzde}',
                'SARJ TIPI':           sarj_map.get(sarj_tipi, sarj_tipi),
                'SARJ FIRMASI ADI':    sarj_firma,
                'KW UCRETI':           str(kw_ucreti).replace('.', ','),
                'UCRET TIPI':          ucret_map.get(ucret_tipi, ucret_tipi),
                'UCRETLI ALINAN KW':   ucretli_kw   if ucretli_kw   > 0 else None,
                'UCRETLI ALIM TUTARI': ucretli_tutar if ucretli_tutar > 0 else None,
                "ACIL OSGB'DEN ALINAN KW":      osgb_kw    if osgb_kw    > 0 else None,
                "ACIL OSGB'YE ODENMEYEN TUTAR": osgb_tutar if osgb_tutar > 0 else None,
                'HEDIYE KW':           hediye_kw    if hediye_kw    > 0 else None,
                'HEDIYE ALIM TUTARI':  hediye_tutar if hediye_tutar > 0 else None,
                'LOKALIZASYON':        lokalizasyon,
                'WLTP MENZIL':         wltp   if wltp   > 0 else None,
                'PROFIL MENZIL':       profil if profil > 0 else None,
                'ACIKLAMA':            aciklama,
                'GERCEK ALINAN KW':    round(gercek_kw, 4),
            }
            save_row(row)
            st.success(f"✅ Kaydedildi! {tarih.strftime('%d.%m.%Y')} — {sarj_firma}")
            st.rerun()

# ===========================================================
# TAB 3 — VERİLER
# ===========================================================
with tab3:
    st.markdown("### 📋 TÜM KAYITLAR")
    if len(df) == 0:
        st.info("Henüz kayıt yok.")
    else:
        show_cols = [
            'TARIH', 'SARJ TIPI', 'SARJ FIRMASI ADI', 'UCRET TIPI',
            'UCRETLI ALINAN KW', 'UCRETLI ALIM TUTARI',
            "ACIL OSGB'DEN ALINAN KW", "ACIL OSGB'YE ODENMEYEN TUTAR",
            'HEDIYE KW', 'HEDIYE ALIM TUTARI',
            'ARAC KM', 'LOKALIZASYON', 'SARJ SURESI (DK)', 'ACIKLAMA'
        ]
        existing = [c for c in show_cols if c in df.columns]
        st.dataframe(df[existing].reset_index(drop=True),
                     use_container_width=True, height=450)

        csv_bytes = df.to_csv(sep=';', index=False,
                              encoding='utf-8-sig').encode('utf-8-sig')
        st.download_button(
            label="⬇️ CSV İNDİR",
            data=csv_bytes,
            file_name="SARJ_VERILERI.csv",
            mime="text/csv",
            use_container_width=True
        )
