import streamlit as st
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
# Auto Refresh setiap 10 detik
# ======================================================
st_autorefresh(interval=10000, key="refresh")

# ======================================================
# Scope Google API
# ======================================================
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# ======================================================
# Membaca JSON
# ======================================================
creds = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=scope
)

# ======================================================
# Login Google Sheets
# ======================================================
client = gspread.authorize(creds)

# ======================================================
# Membuka Spreadsheet
# ======================================================
spreadsheet = client.open("dataset_supermarket")
worksheet = spreadsheet.sheet1

# ======================================================
# Mengambil Data
# ======================================================
data = worksheet.get_all_records()
df = pd.DataFrame(data)

# ======================================================
# Mengubah tipe data
# ======================================================
df["Harga_Satuan"] = pd.to_numeric(df["Harga_Satuan"], errors="coerce")
df["Jumlah"] = pd.to_numeric(df["Jumlah"], errors="coerce")
df["Total_Harga"] = pd.to_numeric(df["Total_Harga"], errors="coerce")
df["Rating"] = pd.to_numeric(df["Rating"], errors="coerce")
df["Tanggal"] = pd.to_datetime(df["Tanggal"])

# ======================================================
# Judul Dashboard
# ======================================================
st.title("📊 Dashboard Penjualan Supermarket")

clock_html = """
<div style="margin-top: 0.4rem; margin-bottom: 1rem; font-size: 1rem; font-weight: 600; color: #0f172a;">
  <div id="live-clock"></div>
</div>
<script>
function updateClock() {
  const now = new Date();
  const date = now.toLocaleDateString("id-ID", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric"
  });
  const time = now.toLocaleTimeString("id-ID", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit"
  });
  document.getElementById("live-clock").innerHTML = "📅 " + date + " &nbsp;&nbsp; 🕒 " + time + " WIB";
}
updateClock();
setInterval(updateClock, 1000);
</script>
"""

st_html(clock_html, height=70)

# ======================================================
# Informasi Dashboard
# ======================================================
st.success("🟢 Google Spreadsheet Connected")
st.caption("🔄 Dashboard melakukan Auto Refresh setiap 10 detik.")

# ======================================================
# Sidebar Filter
# ======================================================
st.sidebar.header("🔍 Filter Data")

cabang = st.sidebar.multiselect(
    "Pilih Cabang",
    options=sorted(df["Cabang"].unique()),
    default=sorted(df["Cabang"].unique())
)

kategori = st.sidebar.multiselect(
    "Pilih Kategori Produk",
    options=sorted(df["Kategori_Produk"].unique()),
    default=sorted(df["Kategori_Produk"].unique())
)

tanggal = st.sidebar.multiselect(
    "Pilih Tanggal",
    options=sorted(df["Tanggal"].dt.strftime("%Y-%m-%d").unique()),
    default=sorted(df["Tanggal"].dt.strftime("%Y-%m-%d").unique())
)

produk = st.sidebar.multiselect(
    "Pilih Nama Produk",
    options=sorted(df["Nama_Produk"].unique()),
    default=sorted(df["Nama_Produk"].unique())
)

metode = st.sidebar.multiselect(
    "Pilih Metode Pembayaran",
    options=sorted(df["Metode_Pembayaran"].unique()),
    default=sorted(df["Metode_Pembayaran"].unique())
)
# ======================================================
# Filter Data
# ======================================================
df_filter = df[
    (df["Cabang"].isin(cabang)) &
    (df["Kategori_Produk"].isin(kategori)) &
    (df["Nama_Produk"].isin(produk)) &
    (df["Metode_Pembayaran"].isin(metode)) &
    (df["Tanggal"].dt.strftime("%Y-%m-%d").isin(tanggal))
]

# ======================================================
# KPI
# ======================================================
total_penjualan = df_filter["Total_Harga"].sum()
total_barang = df_filter["Jumlah"].sum()
rata_rating = df_filter["Rating"].mean()
total_transaksi = len(df_filter)

rata_transaksi = total_penjualan / total_transaksi if total_transaksi > 0 else 0
produk_terjual = df_filter["Nama_Produk"].nunique()

col1, col2, col3 = st.columns(3)
col4, col5, col6 = st.columns(3)

col1.metric(
    "💰 Total Penjualan",
    f"Rp {total_penjualan:,.0f}".replace(",", ".")
)

col2.metric(
    "📦 Total Barang",
    f"{int(total_barang):,}".replace(",", ".")
)

col3.metric(
    "⭐ Rating Rata-rata",
    f"{rata_rating:.2f}"
)

col4.metric(
    "🧾 Total Transaksi",
    total_transaksi
)

col5.metric(
    "🛒 Rata-rata per Transaksi",
    f"Rp {rata_transaksi:,.0f}".replace(",", ".")
)

col6.metric(
    "📦 Jenis Produk",
    produk_terjual
)

st.divider()

# ======================================================
# Visualisasi
# ======================================================
st.subheader("📊 Visualisasi Dashboard")

grafik1, grafik2 = st.columns(2)

# Penjualan per Cabang
sales_cabang = (
    df_filter.groupby("Cabang")["Total_Harga"]
    .sum()
    .reset_index()
)

fig1 = px.bar(
    sales_cabang,
    x="Cabang",
    y="Total_Harga",
    text_auto=True,
    title="Total Penjualan per Cabang"
)

grafik1.plotly_chart(fig1, use_container_width=True)

# Penjualan per Kategori
sales_kategori = (
    df_filter.groupby("Kategori_Produk")["Total_Harga"]
    .sum()
    .reset_index()
)

fig2 = px.bar(
    sales_kategori,
    x="Kategori_Produk",
    y="Total_Harga",
    text_auto=True,
    title="Total Penjualan per Kategori Produk"
)

grafik2.plotly_chart(fig2, use_container_width=True)

grafik3, grafik4 = st.columns(2)

# Pie Chart Metode Pembayaran
payment = (
    df_filter.groupby("Metode_Pembayaran")
    .size()
    .reset_index(name="Jumlah")
)

fig3 = px.pie(
    payment,
    names="Metode_Pembayaran",
    values="Jumlah",
    title="Metode Pembayaran"
)

grafik3.plotly_chart(fig3, use_container_width=True)

# Tren Penjualan
trend = (
    df_filter.groupby("Tanggal")["Total_Harga"]
    .sum()
    .reset_index()
)

fig4 = px.line(
    trend,
    x="Tanggal",
    y="Total_Harga",
    markers=True,
    title="Tren Penjualan"
)

grafik4.plotly_chart(fig4, use_container_width=True)

st.divider()

st.subheader("🏆 Top 10 Produk Terlaris")

top_produk = (
    df_filter.groupby("Nama_Produk")["Jumlah"]
    .sum()
    .sort_values(ascending=False)
    .head(10)
    .reset_index()
)

fig5 = px.bar(
    top_produk,
    x="Jumlah",
    y="Nama_Produk",
    orientation="h",
    color="Jumlah",
    text="Jumlah",
    title="Top 10 Produk Terlaris"
)

fig5.update_layout(
    yaxis_title="",
    xaxis_title="Jumlah Terjual",
    yaxis=dict(categoryorder="total ascending")
)

st.plotly_chart(fig5, use_container_width=True)

st.divider()

st.subheader("💰 Top 10 Produk dengan Omzet Tertinggi")

top_omzet = (
    df_filter.groupby("Nama_Produk")["Total_Harga"]
    .sum()
    .sort_values(ascending=False)
    .head(10)
    .reset_index()
)

fig6 = px.bar(
    top_omzet,
    x="Total_Harga",
    y="Nama_Produk",
    orientation="h",
    color="Total_Harga",
    text_auto=True,
    title="Top 10 Produk Berdasarkan Omzet"
)

fig6.update_layout(
    yaxis_title="",
    xaxis_title="Total Omzet (Rp)",
    yaxis=dict(categoryorder="total ascending")
)

st.plotly_chart(fig6, use_container_width=True)

st.divider()

# ======================================================
# Tabel Data
# ======================================================
st.subheader("📋 Data Penjualan")

# Mengatur urutan kolom
kolom = [
    "Tanggal",
    "Nama_Produk",
    "Kategori_Produk",
    "Cabang",
    "Harga_Satuan",
    "Jumlah",
    "Total_Harga",
    "Metode_Pembayaran",
    "Rating"
]

st.dataframe(
    df_filter[kolom],
    use_container_width=True,
    hide_index=True,
    column_config={
        "Tanggal": st.column_config.DateColumn(
            "Tanggal",
            format="DD-MM-YYYY"
        ),
        "Nama_Produk": st.column_config.TextColumn(
            "Nama Produk",
            width="large"
        ),
        "Kategori_Produk": st.column_config.TextColumn(
            "Kategori",
            width="medium"
        ),
        "Cabang": st.column_config.TextColumn(
            "Cabang",
            width="small"
        ),
        "Harga_Satuan": st.column_config.NumberColumn(
            "Harga Satuan",
            format="Rp %.0f"
        ),
        "Jumlah": st.column_config.NumberColumn(
            "Jumlah"
        ),
        "Total_Harga": st.column_config.NumberColumn(
            "Total Harga",
            format="Rp %.0f"
        ),
        "Metode_Pembayaran": st.column_config.TextColumn(
            "Metode Pembayaran",
            width="medium"
        ),
        "Rating": st.column_config.NumberColumn(
            "Rating",
            format="%.1f ⭐"
        )
    }
)
