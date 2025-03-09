"""\nE-Commerce Data Analysis Dashboard\nOptimized Streamlit code with the following improvements:\n1. Using st_folium to avoid deprecation warnings.\n2. Using st.cache_data() for efficient data loading.\n3. Avoiding empty dataset issues with basic checks.\n4. A modular structure for clarity.\n"""

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium

st.set_page_config(page_title="E-Commerce Data Analysis", layout="wide")

# ================================
# 1. Data Loading with Cache
# ================================

@st.cache_data
def load_data():
    """Load CSV datasets into DataFrames."""
    customer_df = pd.read_csv("customer_dataset.csv")
    geolocation_df = pd.read_csv("geolocation_dataset.csv")
    order_df = pd.read_csv("order_dataset.csv")
    order_items_df = pd.read_csv("order_items_dataset.csv")
    order_payments_df = pd.read_csv("order_payments_dataset.csv")
    product_df = pd.read_csv("product_dataset.csv")
    seller_df = pd.read_csv("seller_dataset.csv")
    return (
        customer_df,
        geolocation_df,
        order_df,
        order_items_df,
        order_payments_df,
        product_df,
        seller_df
    )

# Call the cache function
(
    customer_df,
    geolocation_df,
    order_df,
    order_items_df,
    order_payments_df,
    product_df,
    seller_df
) = load_data()

# ================================
# 2. Data Preprocessing
# ================================
customer_geo = pd.merge(
    customer_df,
    geolocation_df,
    left_on='customer_zip_code_prefix',
    right_on='geolocation_zip_code_prefix',
    how='inner'
)
seller_geo = pd.merge(
    seller_df,
    geolocation_df,
    left_on='seller_zip_code_prefix',
    right_on='geolocation_zip_code_prefix',
    how='inner'
)

# ================================
# 3. Streamlit Layout & Navigation
# ================================
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Go to",
    [
        "Sale Trend",
        "Late Orders Analysis",
        "Payment Method Analysis",
        "City-wise Distribution"
    ]
)

# ================================
# 4. Page Implementations
# ================================

def page_sale_trend():
    st.header("Pertanyaan 1: Bagaimana trend penjualan di E-commerce di rentang tanggal tertentu?")
    st.subheader("Visualisasi: Tren Penjualan")

    merged_orders = pd.merge(order_df, order_items_df, on="order_id", how="inner")
    # Convert date
    merged_orders["order_delivered_customer_date"] = pd.to_datetime(
        merged_orders["order_delivered_customer_date"]
    )

    # Check if DataFrame is empty
    if merged_orders.empty:
        st.error("Data orders tidak tersedia.")
        return

    # Date range filter
    min_date = merged_orders["order_delivered_customer_date"].min().date()
    max_date = merged_orders["order_delivered_customer_date"].max().date()

    selected_date_range = st.date_input(
        "Pilih rentang tanggal untuk melihat jumlah item terjual per hari:",
        [min_date, max_date]
    )

    if len(selected_date_range) == 2:
        start_date, end_date = selected_date_range
        if start_date > end_date:
            st.warning("Tanggal awal harus lebih kecil atau sama dengan tanggal akhir.")
        else:
            mask = (
                (merged_orders["order_delivered_customer_date"] >= pd.to_datetime(start_date)) &
                (merged_orders["order_delivered_customer_date"] <= pd.to_datetime(end_date))
            )
            range_data = merged_orders[mask]

            if range_data.empty:
                st.info("Tidak ada pesanan di rentang tanggal yang dipilih.")
            else:
                # Group by day and count items
                daily_item_count = (
                    range_data
                    .groupby(range_data["order_delivered_customer_date"].dt.date)["order_item_id"]
                    .count()
                )

                fig, ax = plt.subplots(figsize=(10, 5))
                ax.plot(
                    pd.to_datetime(daily_item_count.index),
                    daily_item_count.values,
                    marker='o',
                    linestyle='-',
                    color='orange'
                )
                ax.set_title("Daily Item Sold in Selected Date Range")
                ax.set_xlabel("Delivery Date")
                ax.set_ylabel("Number of Items Sold")
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%b, %Y'))
                ax.grid(True, alpha=0.3)

                st.pyplot(fig)
                st.markdown("**Insight:**")
                st.markdown(
                    """
                    - Pada periode akhir 2016 hingga awal 2017, jumlah item yang terjual per hari masih relatif rendah. Namun, seiring berjalannya waktu (mulai memasuki pertengahan 2017), terlihat peningkatan baik dari segi frekuensi maupun volume penjualan harian.
                    - Memasuki pertengahan 2017 hingga awal 2018, grafik menunjukkan lonjakan signifikan dengan beberapa hari mencapai penjualan di atas 300–500 item. Hal ini bisa disebabkan oleh faktor promosi, musim belanja tertentu (mis. liburan, akhir tahun), atau peningkatan jumlah pelanggan.
                    - Terdapat beberapa lonjakan di bulan-bulan tertentu saja yang bisa berkaitan dengan dampak dari musim dingin, hingga penerapan diskon atau kupon, namun secara garis besar trend penjualan sangat baik karena meningkat setiap kuartalnya.
                    - Peningkatan kualitas pelayanan e-commerce, seiring dengan meningkatnya tren pembelian, membuka peluang besar untuk membangun kepercayaan serta memperluas penguasaan pasar, baik di kalangan pelanggan baru maupun pelanggan lama
                    """
                )


def page_late_orders_analysis():
    st.header("Pertanyaan 2: Berapa persentase pesanan yang terlambat sampai ke pelanggan?")

    # Convert date
    order_df['order_estimated_delivery_date'] = pd.to_datetime(order_df['order_estimated_delivery_date'])
    order_df['order_delivered_customer_date'] = pd.to_datetime(order_df['order_delivered_customer_date'])

    delivered_orders = order_df[order_df['order_status'] == 'delivered'].copy()

    if delivered_orders.empty:
        st.error("Tidak ada data pesanan yang sudah dikirim.")
        return

    # Flag lateness
    delivered_orders['late_delivery'] = (
        delivered_orders['order_delivered_customer_date'] > delivered_orders['order_estimated_delivery_date']
    )

    late_percentage = delivered_orders['late_delivery'].mean() * 100

    # Pie chart
    st.subheader("Visualisasi 1: Pie Chart On-Time vs Late")
    labels = ['On Time', 'Late']
    sizes = [100 - late_percentage, late_percentage]
    colors = ['#4CAF50', '#F44336']
    explode = (0.1, 0)

    fig, ax = plt.subplots(figsize=(4, 4))
    ax.pie(
        sizes,
        labels=labels,
        autopct='%1.1f%%',
        startangle=140,
        colors=colors,
        explode=explode
    )
    ax.set_title("Percentage of Orders Delivered On Time vs Late")
    st.pyplot(fig)

    st.markdown("**Insight (Pie Chart):**")
    st.markdown(
        f"""
        - Mayoritas pesanan (sekitar {100 - late_percentage:.1f}%) dikirim tepat waktu.\n
        - Faktor keterlambatan yang tersisa (sekitar {late_percentage:.1f}%) bisa disebabkan\\\
          oleh jarak pengiriman, logistik, maupun adanya lonjakan pembelian yang terlalu tinggi sehingga kurang adanya persiapan.
        """
    )

    # Time series of lateness
    st.subheader("Visualisasi 2: Time Series Keterlambatan Pengiriman")
    orders_by_date = delivered_orders.groupby(
        delivered_orders['order_delivered_customer_date'].dt.date
    ).size()

    late_orders_by_date = delivered_orders[
        delivered_orders['late_delivery']
    ].groupby(
        delivered_orders['order_delivered_customer_date'].dt.date
    ).size()

    # Convert index to datetime
    orders_by_date.index = pd.to_datetime(orders_by_date.index)
    late_orders_by_date.index = pd.to_datetime(late_orders_by_date.index)

    orders_by_date_sma = orders_by_date.rolling(window=7).mean()
    late_orders_by_date_sma = late_orders_by_date.rolling(window=7).mean()

    fig, ax = plt.subplots(figsize=(10,5))
    ax.plot(
        orders_by_date.index,
        orders_by_date.values,
        marker='o',
        linestyle='-',
        color='lightblue',
        alpha=0.6,
        label="Daily Orders"
    )
    ax.plot(
        orders_by_date_sma.index,
        orders_by_date_sma.values,
        linestyle='-',
        color='blue',
        linewidth=2,
        label="7-Day Moving Avg - Orders"
    )
    ax.plot(
        late_orders_by_date.index,
        late_orders_by_date.values,
        marker='o',
        linestyle='-',
        color='lightcoral',
        alpha=0.6,
        label="Daily Late Orders"
    )
    ax.plot(
        late_orders_by_date_sma.index,
        late_orders_by_date_sma.values,
        linestyle='-',
        color='red',
        linewidth=2,
        label="7-Day Moving Avg - Late Orders"
    )

    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    ax.set_xlabel("Delivery Date (Month-Year)")
    ax.set_ylabel("Number of Orders")
    ax.set_title("Orders Delivered & Late Orders Over Time with Trend")
    ax.legend()
    ax.grid(alpha=0.3)
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")

    st.pyplot(fig)

    st.markdown("**Insight (Time Series):**")
    st.markdown(
        """
        - Bisa diketahui bahwa setiap adanya peningkatan pembelian, maka setelahnya akan diikuti semakin banyaknya barang terlambat.\n
        - Kemudian, setelah adanya peningkatan jumlah barang terlambat, akan menyebabnya pembelian di E-commerce tersebut menurun. Hal ini bisa dikarenakan menurunnya kepercayaan pada platform E-commerce tersebut.
        """
    )


def page_payment_method_analysis():
    st.header("Pertanyaan 3: Metode pembayaran mana yang paling banyak digunakan dan mana yang paling jarang digunakan?")

    if order_payments_df.empty:
        st.error("Data payment tidak tersedia.")
        return

    payment_counts = order_payments_df['payment_type'].value_counts()

    # Visualization: Pie Chart
    st.subheader("Visualisasi: Payment Method Usage Distribution")
    clean_labels = [lbl.replace("_", " ").title() for lbl in payment_counts.index]

    fig, ax = plt.subplots(figsize=(4,4))
    ax.pie(
        payment_counts,
        labels=clean_labels,
        autopct='%1.1f%%',
        startangle=140
    )
    ax.set_title("Payment Method Usage Distribution")
    st.pyplot(fig)

    st.markdown("**Insight (Payment Method Analysis):**")
    st.markdown(
        """
        - Metode pembayaran yang paling banyak digunakan adalah Credit Card.\n
        - Boleto juga menempati posisi yang cukup signifikan.\n
        - Metode lain seperti Voucher dan Debit Card memiliki proporsi yang lebih kecil.\n
        - Mengadakan campaign atau program voucher atau kupon untuk pengguna credit card bisa meningkatkan penjualan karena banyaknya orang yang menggunakan metode pembayaran tersebut.
        """
    )


def page_city_distribution():
    st.header("Pertanyaan 4: Kota mana yang memiliki jumlah pelanggan terbanyak dan kota mana yang memiliki jumlah penjual terbanyak?")

    # Bar Chart: Top 10 Cities (Customers)
    st.subheader("Visualisasi 1: Top 10 Cities with Most Customers")
    if customer_df.empty:
        st.error("Data customer tidak tersedia.")
        return

    city_customer_counts = (
        customer_df['customer_city']
        .str.title()
        .value_counts()
        .head(10)
    )

    fig, ax = plt.subplots(figsize=(8,5))
    city_customer_counts.plot(kind='barh', ax=ax, color='royalblue')
    ax.set_title("Top 10 Cities with Most Customers")
    ax.set_xlabel("Number of Customers")
    ax.set_ylabel("City")
    st.pyplot(fig)

    st.markdown("**Insight (Top 10 Cities - Customers):**")
    st.markdown(
        """
        - Kota dengan jumlah pelanggan terbanyak biasanya kota besar atau pusat bisnis, seperti São Paulo atau Rio de Janeiro.\n
        - Distribusi pelanggan umumnya terpusat di wilayah tenggara Brasil.
        """
    )

    # Heatmaps (Customer & Seller Density)
    st.subheader("Visualisasi 2: Heatmap Customer & Seller")
    if customer_geo.empty or seller_geo.empty:
        st.error("Data lokasi customer/seller tidak tersedia.")
        return

    # Prepare geo data
    customer_counts_geo = customer_geo.groupby(["geolocation_lat", "geolocation_lng"]).size().reset_index(name="customer_count")
    seller_counts_geo = seller_geo.groupby(["geolocation_lat", "geolocation_lng"]).size().reset_index(name="seller_count")

    # Folium maps
    customer_map = folium.Map(location=[-23.55, -46.63], zoom_start=5)
    seller_map = folium.Map(location=[-23.55, -46.63], zoom_start=5)

    # Heatmap data
    heat_data_customers = list(zip(
        customer_counts_geo["geolocation_lat"],
        customer_counts_geo["geolocation_lng"],
        customer_counts_geo["customer_count"]
    ))
    heat_data_sellers = list(zip(
        seller_counts_geo["geolocation_lat"],
        seller_counts_geo["geolocation_lng"],
        seller_counts_geo["seller_count"]
    ))

    HeatMap(
        heat_data_customers,
        name="Customer Density",
        radius=15
    ).add_to(customer_map)

    HeatMap(
        heat_data_sellers,
        name="Seller Density",
        radius=15
    ).add_to(seller_map)

    st.markdown("**Customer Density Map**")
    st_folium(customer_map)

    st.markdown("**Seller Density Map**")
    st_folium(seller_map)

    st.markdown("**Insight (Heatmaps):**")
    st.markdown(
        """
        - Peta kepadatan pelanggan dan penjual memperlihatkan konsentrasi tertinggi\n
          di area perkotaan padat penduduk.\n
        - Dengan mengetahui lokasi penjual dan pelanggan, dapat dioptimalkan\n
          strategi pengiriman dan penyebaran gudang, terutama di daerah dengan pembeli yang banyak.\n
        - Adanya pembeli dari luar Amerika Selatan membuka peluang untuk ekspansi global.
        """
    )

# ================================
# 5. Render Pages
# ================================

if page == "Sale Trend":
    page_sale_trend()
elif page == "Late Orders Analysis":
    page_late_orders_analysis()
elif page == "Payment Method Analysis":
    page_payment_method_analysis()
elif page == "City-wise Distribution":
    page_city_distribution()