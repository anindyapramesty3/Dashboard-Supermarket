import streamlit as st
import os
from streamlit_autorefresh import st_autorefresh
from streamlit.components.v1 import html as st_html
import pandas as pd
import plotly.express as px
import gspread
from google.oauth2.service_account import Credentials

# ======================================================
# Konfigurasi Halaman
# ======================================================
st.set_page_config(
    page_title="Dashboard Supermarket",
    page_icon="📊",
    layout="wide"
)

# ======================================================
# Tema & Palet Warna
# ======================================================
CATEGORICAL = ["#2a78d6", "#008300", "#e87ba4", "#eda100", "#1baf7a", "#eb6834", "#4a3aa7", "#e34948"]
SEQUENTIAL_BLUE = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#2a78d6", "#1c5cab", "#104281"]

px.defaults.template = "plotly_white"
px.defaults.color_discrete_sequence = CATEGORICAL
px.defaults.color_continuous_scale = SEQUENTIAL_BLUE

def style_fig(fig):
    fig.update_layout(
        font=dict(family="system-ui, -apple-system, 'Segoe UI', sans-serif", color="#0b0b0b", size=13),
        title_font=dict(size=16, color="#0b0b0b"),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=55, l=10, r=10, b=10),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
        hoverlabel=dict(bgcolor="white", font_size=13),
        transition=dict(duration=500, easing="cubic-in-out"),
    )
    fig.update_xaxes(showgrid=False, linecolor="#c3c2b7")
    fig.update_yaxes(showgrid=True, gridcolor="#e1e0d9", zeroline=False)
    return fig

# Custom CSS
st.markdown("""
<style>
:root{
  --surface: #fcfcfb;
  --page: #f9f9f7;
  --ink: #0b0b0b;
  --ink-secondary: #52514e;
  --border: rgba(11,11,11,0.10);
  --accent: #2a78d6;
}
@media (prefers-color-scheme: dark){
  :root{
    --surface: #fff8e1;
    --page: #ffc914;
    --ink: #241c00;
    --ink-secondary: #5c4b00;
    --border: rgba(36,28,0,0.15);
    --accent: #2a78d6;
  }
}

[data-testid="stAppViewContainer"]{ background-color: var(--page); }
.block-container{ padding-top: 1.5rem; padding-bottom: 3rem; max-width: 1300px; }

[data-testid="stSidebar"]{
  background-color: var(--surface);
  border-right: 1px solid var(--border);
}

h2, h3{
  font-weight: 700;
  color: var(--ink);
  border-left: 4px solid var(--accent);
  padding-left: 0.6rem;
  margin-top: 1.6rem !important;
}

hr{ border-color: var(--border) !important; }
.stAlert{ border-radius: 10px; }

/* Hero banner */
.hero-banner{
  background: linear-gradient(135deg, #2a78d6 0%, #4a3aa7 100%);
  border-radius: 18px;
  padding: 26px 32px;
  margin-bottom: 1rem;
  box-shadow: 0 10px 28px rgba(42,120,214,0.28);
}
.hero-title{
  font-size: 2rem;
  font-weight: 800;
  color: #ffffff;
  letter-spacing: -0.02em;
}
.hero-subtitle{
  font-size: 1rem;
  font-weight: 500;
  color: rgba(255,255,255,0.88);
  margin-top: 4px;
}

/* KPI cards */
.kpi-grid{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
  gap: 14px;
  margin: 0.6rem 0 1.4rem 0;
}
.kpi-card{
  background: color-mix(in srgb, var(--card-accent) 12%, var(--surface));
  border: 1px solid color-mix(in srgb, var(--card-accent) 35%, var(--border));
  border-left: 6px solid var(--card-accent);
  border-radius: 14px;
  padding: 16px 18px;
  box-shadow: 0 2px 8px rgba(11,11,11,0.06);
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}
.kpi-card:hover{
  transform: translateY(-3px);
  box-shadow: 0 10px 22px color-mix(in srgb, var(--card-accent) 30%, transparent);
}
.kpi-icon-badge{
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: var(--card-accent);
  font-size: 1.05rem;
  margin-bottom: 10px;
  box-shadow: 0 4px 10px color-mix(in srgb, var(--card-accent) 45%, transparent);
}
.kpi-value{ font-size: 1.55rem; font-weight: 800; color: var(--ink); line-height: 1.2; }
.kpi-label{ font-size: 0.85rem; color: var(--ink-secondary); margin-top: 2px; }

/* Container visualisasi */
div[data-testid="stVerticalBlockBorderWrapper"]{
  border-radius: 16px !important;
  border: 1px solid var(--border) !important;
  background-color: var(--surface) !important;
  box-shadow: 0 1px 3px rgba(11,11,11,0.06);
  padding: 6px;
}

[data-testid="stDataFrame"]{ border-radius: 12px; overflow: hidden; }
</style>
""", unsafe_allow_html=True)

# ======================================================
# Auto Refresh (Setiap 10 Detik)
# ======================================================
st_autorefresh(interval=10000, key="refresh")

# ======================================================
# Caching Koneksi & Pengambilan Data (Mencegah Rate Limit)
# ======================================================
@st.cache_resource
def get_gspread_client():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    if os.path.exists("dashboard-supermarket-502503-f85341cff5cb.json"):
        creds = Credentials.from_service_account_file(
            "dashboard-supermarket-502503-f85341cff5cb.json",
            scopes=scope
        )
    else:
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=scope
        )
    return gspread.authorize(creds)

@st.cache_data(ttl=10)
def fetch_data():
    client = get_gspread_client()
    spreadsheet = client.open("dataset_supermarket")
    worksheet = spreadsheet.sheet1
    data = worksheet.get_all_records()
    df_raw = pd.DataFrame(data)

    # Konversi tipe data
    df_raw["Harga_Satuan"] = pd.to_numeric(df_raw["Harga_Satuan"], errors="coerce")
    df_raw["Jumlah"] = pd.to_numeric(df_raw["Jumlah"], errors="coerce")
    df_raw["Total_Harga"] = pd.to_numeric(df_raw["Total_Harga"], errors="coerce")
    df_raw["Rating"] = pd.to_numeric(df_raw["Rating"], errors="coerce")
    df_raw["Tanggal"] = pd.to_datetime(df_raw["Tanggal"])
    return df_raw

try:
    df = fetch_data()
except Exception as e:
    st.error(f"⚠️ Gagal menghubungkan ke Google Sheets: {e}")
    st.stop()

# ======================================================
# Header & Jam Live
# ======================================================
st.markdown("""
<div class="hero-banner">
  <div class="hero-title">📊 Dashboard Penjualan Supermarket</div>
  <div class="hero-subtitle">Insight penjualan real-time dari seluruh cabang</div>
</div>
""", unsafe_allow_html=True)

clock_html = """
<style>
  @media (prefers-color-scheme: dark) {
    body { background-color: transparent; }
    .clock-badge { background: #fff8e1 !important; border-color: rgba(36,28,0,0.15) !important; color: #241c00 !important; }
  }
  body { margin: 0; font-family: system-ui, -apple-system, "Segoe UI", sans-serif; }
  .clock-badge {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    margin-top: 0.3rem;
    padding: 8px 16px;
    border-radius: 999px;
    background: #fcfcfb;
    border: 1px solid rgba(11,11,11,0.10);
    font-size: 0.95rem;
    font-weight: 600;
    color: #0b0b0b;
  }
</style>
<div class="clock-badge">
  <div id="live-clock"></div>
</div>
<script>
function updateClock() {
  const now = new Date();
  const date = now.toLocaleDateString("id-ID", { day: "2-digit", month: "2-digit", year: "numeric" });
  const time = now.toLocaleTimeString("id-ID", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
  document.getElementById("live-clock").innerHTML = "📅 " + date + " &nbsp;&nbsp; 🕒 " + time + " WIB";
}
updateClock();
setInterval(updateClock, 1000);
</script>
"""
st_html(clock_html, height=60)

st.success("🟢 Google Spreadsheet Connected")
st.caption("🔄 Dashboard melakukan Auto Refresh data setiap 10 detik.")

# ======================================================
# Sidebar Filter Data
# ======================================================
st.sidebar.header("🔍 Filter Data")

cabang_opts = sorted(df["Cabang"].dropna().unique())
kategori_opts = sorted(df["Kategori_Produk"].dropna().unique())
tanggal_opts = sorted(df["Tanggal"].dt.strftime("%Y-%m-%d").dropna().unique())
produk_opts = sorted(df["Nama_Produk"].dropna().unique())
metode_opts = sorted(df["Metode_Pembayaran"].dropna().unique())

cabang = st.sidebar.multiselect("Pilih Cabang", options=cabang_opts, default=cabang_opts)
kategori = st.sidebar.multiselect("Pilih Kategori Produk", options=kategori_opts, default=kategori_opts)
tanggal = st.sidebar.multiselect("Pilih Tanggal", options=tanggal_opts, default=tanggal_opts)
produk = st.sidebar.multiselect("Pilih Nama Produk", options=produk_opts, default=produk_opts)
metode = st.sidebar.multiselect("Pilih Metode Pembayaran", options=metode_opts, default=metode_opts)

# ======================================================
# Filter Dataframe
# ======================================================
df_filter = df[
    (df["Cabang"].isin(cabang)) &
    (df["Kategori_Produk"].isin(kategori)) &
    (df["Nama_Produk"].isin(produk)) &
    (df["Metode_Pembayaran"].isin(metode)) &
    (df["Tanggal"].dt.strftime("%Y-%m-%d").isin(tanggal))
]

# ======================================================
# Kalkulasi KPI Card
# ======================================================
total_penjualan = df_filter["Total_Harga"].sum()
total_barang = df_filter["Jumlah"].sum()
rata_rating = df_filter["Rating"].mean() if not df_filter["Rating"].isna().all() else 0
total_transaksi = len(df_filter)
rata_transaksi = total_penjualan / total_transaksi if total_transaksi > 0 else 0
produk_terjual = df_filter["Nama_Produk"].nunique()

kpi_data = [
    {"icon": "💰", "label": "Total Penjualan", "value": f"Rp {total_penjualan:,.0f}".replace(",", "."), "color": CATEGORICAL[0]},
    {"icon": "📦", "label": "Total Barang", "value": f"{int(total_barang):,}".replace(",", "."), "color": CATEGORICAL[1]},
    {"icon": "⭐", "label": "Rating Rata-rata", "value": f"{rata_rating:.2f}", "color": CATEGORICAL[3]},
    {"icon": "🧾", "label": "Total Transaksi", "value": f"{total_transaksi:,}".replace(",", "."), "color": CATEGORICAL[4]},
    {"icon": "🛒", "label": "Rata-rata per Transaksi", "value": f"Rp {rata_transaksi:,.0f}".replace(",", "."), "color": CATEGORICAL[5]},
    {"icon": "📦", "label": "Jenis Produk", "value": f"{produk_terjual:,}".replace(",", "."), "color": CATEGORICAL[6]},
]

kpi_cards = "".join(
    f"""<div class="kpi-card" style="--card-accent:{k['color']}">
        <div class="kpi-icon-badge">{k['icon']}</div>
        <div class="kpi-value">{k['value']}</div>
        <div class="kpi-label">{k['label']}</div>
    </div>"""
    for k in kpi_data
)

st.markdown(f'<div class="kpi-grid">{kpi_cards}</div>', unsafe_allow_html=True)
st.divider()

# ======================================================
# Visualisasi Data
# ======================================================
st.subheader("📊 Visualisasi Dashboard")

grafik1, grafik2 = st.columns(2)

# 1. Total Penjualan per Cabang
sales_cabang = df_filter.groupby("Cabang", as_index=False)["Total_Harga"].sum()
fig1 = px.bar(sales_cabang, x="Cabang", y="Total_Harga", text_auto=True, title="Total Penjualan per Cabang")
fig1.update_traces(marker_color=CATEGORICAL[0], textposition="outside")
style_fig(fig1)

with grafik1:
    with st.container(border=True):
        st.plotly_chart(fig1, use_container_width=True, key="fig1")

# 2. Total Penjualan per Kategori
sales_kategori = df_filter.groupby("Kategori_Produk", as_index=False)["Total_Harga"].sum()
fig2 = px.bar(sales_kategori, x="Kategori_Produk", y="Total_Harga", text_auto=True, title="Total Penjualan per Kategori Produk")
fig2.update_traces(marker_color=CATEGORICAL[4], textposition="outside")
style_fig(fig2)

with grafik2:
    with st.container(border=True):
        st.plotly_chart(fig2, use_container_width=True, key="fig2")

grafik3, grafik4 = st.columns(2)

# 3. Donut Chart Metode Pembayaran
payment = df_filter.groupby("Metode_Pembayaran", as_index=False).size().rename(columns={"size": "Jumlah"})
fig3 = px.pie(payment, names="Metode_Pembayaran", values="Jumlah", title="Metode Pembayaran", hole=0.45)
fig3.update_traces(marker=dict(line=dict(color="#fcfcfb", width=2)))
style_fig(fig3)

with grafik3:
    with st.container(border=True):
        st.plotly_chart(fig3, use_container_width=True, key="fig3")

# 4. Tren Penjualan Harian
trend = df_filter.groupby("Tanggal", as_index=False)["Total_Harga"].sum()
fig4 = px.line(trend, x="Tanggal", y="Total_Harga", markers=True, title="Tren Penjualan")
fig4.update_traces(line_color=CATEGORICAL[6], marker=dict(size=8, color=CATEGORICAL[6]))
style_fig(fig4)

with grafik4:
    with st.container(border=True):
        st.plotly_chart(fig4, use_container_width=True, key="fig4")

st.divider()

# 5. Top 10 Produk Terlaris
st.subheader("🏆 Top 10 Produk Terlaris")
top_produk = (
    df_filter.groupby("Nama_Produk", as_index=False)["Jumlah"]
    .sum()
    .sort_values(by="Jumlah", ascending=False)
    .head(10)
)
fig5 = px.bar(top_produk, x="Jumlah", y="Nama_Produk", orientation="h", color="Jumlah", text="Jumlah", title="Top 10 Produk Terlaris")
fig5.update_layout(yaxis_title="", xaxis_title="Jumlah Terjual", yaxis=dict(categoryorder="total ascending"), coloraxis_showscale=False)
fig5.update_traces(textposition="outside")
style_fig(fig5)

with st.container(border=True):
    st.plotly_chart(fig5, use_container_width=True, key="fig5")

st.divider()

# 6. Top 10 Produk Omzet Tertinggi
st.subheader("💰 Top 10 Produk dengan Omzet Tertinggi")
top_omzet = (
    df_filter.groupby("Nama_Produk", as_index=False)["Total_Harga"]
    .sum()
    .sort_values(by="Total_Harga", ascending=False)
    .head(10)
)
fig6 = px.bar(top_omzet, x="Total_Harga", y="Nama_Produk", orientation="h", color="Total_Harga", text_auto=True, title="Top 10 Produk Berdasarkan Omzet")
fig6.update_layout(yaxis_title="", xaxis_title="Total Omzet (Rp)", yaxis=dict(categoryorder="total ascending"), coloraxis_showscale=False)
fig6.update_traces(textposition="outside")
style_fig(fig6)

with st.container(border=True):
    st.plotly_chart(fig6, use_container_width=True, key="fig6")

st.divider()

# ======================================================
# Tabel Data Penjualan
# ======================================================
st.subheader("📋 Data Penjualan")

kolom = [
    "Tanggal", "Nama_Produk", "Kategori_Produk", "Cabang",
    "Harga_Satuan", "Jumlah", "Total_Harga", "Metode_Pembayaran", "Rating"
]

with st.container(border=True):
    st.dataframe(
        df_filter[kolom],
        use_container_width=True,
        hide_index=True,
        column_config={
            "Tanggal": st.column_config.DateColumn("Tanggal", format="DD-MM-YYYY"),
            "Nama_Produk": st.column_config.TextColumn("Nama Produk", width="large"),
            "Kategori_Produk": st.column_config.TextColumn("Kategori", width="medium"),
            "Cabang": st.column_config.TextColumn("Cabang", width="small"),
            "Harga_Satuan": st.column_config.NumberColumn("Harga Satuan", format="Rp %.0f"),
            "Jumlah": st.column_config.NumberColumn("Jumlah"),
            "Total_Harga": st.column_config.NumberColumn("Total Harga", format="Rp %.0f"),
            "Metode_Pembayaran": st.column_config.TextColumn("Metode Pembayaran", width="medium"),
            "Rating": st.column_config.NumberColumn("Rating", format="%.1f ⭐")
        }
    )
