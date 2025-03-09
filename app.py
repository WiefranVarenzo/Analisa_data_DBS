import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pydeck as pdk

st.set_page_config(page_title="E-Commerce Data Analysis", layout="wide")

# ================================
# 1. Data Loading dengan Cache
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

customer_df, geolocation_df, order_df, order_items_df, order_payments_df, product_df, seller_df = load_data()

# ================================
# 2. Data Preprocessing dengan Cache
# ================================
@st.cache_data
def merge_geolocation(customer_df, geolocation_df, seller_df):
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
    return customer_geo, seller_geo

customer_geo, seller_geo = merge_geolocation(customer_df, geolocation_df, seller_df)

@st.cache_data
def merge_orders(order_df, order_items_df):
    merged_orders = pd.merge(order_df, order_items_df, on="order_id", how="inner")
    merged_orders["order_delivered_customer_date"] = pd.to_datetime(merged_orders["order_delivered_customer_date"])
    return merged_orders

merged_orders = merge_orders(order_df, order_items_df)

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
                daily_item_count = range_data.groupby(
                    range_data["order_delivered_customer_date"].dt.date
                )["order_item_id"].count()

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
                    - Pada periode akhir 2016 hingga awal 2017, jumlah item yang terjual per hari masih relatif rendah.
                    - Mulai pertengahan 2017 hingga awal 2018, terjadi lonjakan penjualan yang signifikan.
                    - Lonjakan ini mungkin dipicu oleh promosi, musim belanja, atau peningkatan jumlah pelanggan.
                    """
                )

def page_late_orders_analysis():
    st.header("Pertanyaan 2: Berapa persentase pesanan yang terlambat sampai ke pelanggan?")

    # Pastikan konversi tanggal
    order_df['order_estimated_delivery_date'] = pd.to_datetime(order_df['order_estimated_delivery_date'])
    order_df['order_delivered_customer_date'] = pd.to_datetime(order_df['order_delivered_customer_date'])

    delivered_orders = order_df[order_df['order_status'] == 'delivered'].copy()

    if delivered_orders.empty:
        st.error("Tidak ada data pesanan yang sudah dikirim.")
        return

    delivered_orders['late_delivery'] = delivered_orders['order_delivered_customer_date'] > delivered_orders['order_estimated_delivery_date']
    late_percentage = delivered_orders['late_delivery'].mean() * 100

    st.subheader("Visualisasi 1: Pie Chart On-Time vs Late")
    labels = ['On Time', 'Late']
    sizes = [100 - late_percentage, late_percentage]
    colors = ['#4CAF50', '#F44336']
    explode = (0.1, 0)

    fig, ax = plt.subplots(figsize=(4, 4))
    ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140, colors=colors, explode=explode)
    ax.set_title("Percentage of Orders Delivered On Time vs Late")
    st.pyplot(fig)

    st.markdown("**Insight (Pie Chart):**")
    st.markdown(
        f"""
        - Mayoritas pesanan (sekitar {100 - late_percentage:.1f}%) dikirim tepat waktu.
        - Sekitar {late_percentage:.1f}% pesanan terlambat, mungkin disebabkan oleh jarak pengiriman atau lonjakan pembelian.
        """
    )

    st.subheader("Visualisasi 2: Time Series Keterlambatan Pengiriman")
    orders_by_date = delivered_orders.groupby(delivered_orders['order_delivered_customer_date'].dt.date).size()
    late_orders_by_date = delivered_orders[delivered_orders['late_delivery']].groupby(delivered_orders['order_delivered_customer_date'].dt.date).size()

    orders_by_date.index = pd.to_datetime(orders_by_date.index)
    late_orders_by_date.index = pd.to_datetime(late_orders_by_date.index)

    orders_by_date_sma = orders_by_date.rolling(window=7).mean()
    late_orders_by_date_sma = late_orders_by_date.rolling(window=7).mean()

    fig, ax = plt.subplots(figsize=(10,5))
    ax.plot(orders_by_date.index, orders_by_date.values, marker='o', linestyle='-', color='lightblue', alpha=0.6, label="Daily Orders")
    ax.plot(orders_by_date_sma.index, orders_by_date_sma.values, linestyle='-', color='blue', linewidth=2, label="7-Day Moving Avg - Orders")
    ax.plot(late_orders_by_date.index, late_orders_by_date.values, marker='o', linestyle='-', color='lightcoral', alpha=0.6, label="Daily Late Orders")
    ax.plot(late_orders_by_date_sma.index, late_orders_by_date_sma.values, linestyle='-', color='red', linewidth=2, label="7-Day Moving Avg - Late Orders")

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
        - Peningkatan pesanan sering diikuti oleh peningkatan keterlambatan pengiriman.
        - Tren ini bisa menunjukkan perlunya peningkatan logistik atau penyesuaian strategi pengiriman.
        """
    )

def page_payment_method_analysis():
    st.header("Pertanyaan 3: Metode pembayaran mana yang paling banyak digunakan dan mana yang paling jarang digunakan?")

    if order_payments_df.empty:
        st.error("Data payment tidak tersedia.")
        return

    payment_counts = order_payments_df['payment_type'].value_counts()
    st.subheader("Visualisasi: Payment Method Usage Distribution")
    clean_labels = [lbl.replace("_", " ").title() for lbl in payment_counts.index]

    fig, ax = plt.subplots(figsize=(4,4))
    ax.pie(payment_counts, labels=clean_labels, autopct='%1.1f%%', startangle=140)
    ax.set_title("Payment Method Usage Distribution")
    st.pyplot(fig)

    st.markdown("**Insight (Payment Method Analysis):**")
    st.markdown(
        """
        - Credit Card merupakan metode pembayaran yang paling dominan.
        - Metode lain seperti Voucher dan Debit Card memiliki proporsi yang lebih kecil.
        """
    )

def page_city_distribution():
    st.header("Pertanyaan 4: Kota mana yang memiliki jumlah pelanggan terbanyak dan kota mana yang memiliki jumlah penjual terbanyak?")

    st.subheader("Visualisasi 1: Top 10 Cities with Most Customers")
    if customer_df.empty:
        st.error("Data customer tidak tersedia.")
        return

    city_customer_counts = customer_df['customer_city'].str.title().value_counts().head(10)
    fig, ax = plt.subplots(figsize=(8,5))
    city_customer_counts.plot(kind='barh', ax=ax, color='royalblue')
    ax.set_title("Top 10 Cities with Most Customers")
    ax.set_xlabel("Number of Customers")
    ax.set_ylabel("City")
    st.pyplot(fig)

    st.markdown("**Insight (Top 10 Cities - Customers):**")
    st.markdown(
        """
        - Kota besar seperti São Paulo atau Rio de Janeiro mendominasi jumlah pelanggan.
        - Distribusi pelanggan umumnya terpusat di wilayah tenggara Brasil.
        """
    )

    st.subheader("Visualisasi 2: Heatmap Customer & Seller")
    if customer_geo.empty or seller_geo.empty:
        st.error("Data lokasi customer/seller tidak tersedia.")
        return

    customer_counts_geo = customer_geo.groupby(["geolocation_lat", "geolocation_lng"]).size().reset_index(name="customer_count")
    seller_counts_geo = seller_geo.groupby(["geolocation_lat", "geolocation_lng"]).size().reset_index(name="seller_count")

    customer_layer = pdk.Layer(
        "HeatmapLayer",
        data=customer_counts_geo,
        get_position='[geolocation_lng, geolocation_lat]',
        get_weight="customer_count",
        radiusPixels=50,
        aggregation="SUM"
    )

    customer_view = pdk.ViewState(latitude=-23.55, longitude=-46.63, zoom=5, pitch=0)
    customer_deck = pdk.Deck(initial_view_state=customer_view, layers=[customer_layer], tooltip={"text": "Customer Count: {customer_count}"})

    st.markdown("**Customer Density Map**")
    st.pydeck_chart(customer_deck)

    seller_layer = pdk.Layer(
        "HeatmapLayer",
        data=seller_counts_geo,
        get_position='[geolocation_lng, geolocation_lat]',
        get_weight="seller_count",
        radiusPixels=50,
        aggregation="SUM"
    )

    seller_view = pdk.ViewState(latitude=-23.55, longitude=-46.63, zoom=5, pitch=0)
    seller_deck = pdk.Deck(initial_view_state=seller_view, layers=[seller_layer], tooltip={"text": "Seller Count: {seller_count}"})

    st.markdown("**Seller Density Map**")
    st.pydeck_chart(seller_deck)

    st.markdown("**Insight (Heatmaps):**")
    st.markdown(
        """
        - Peta menunjukkan konsentrasi pelanggan dan penjual di area perkotaan padat.
        - Informasi ini dapat membantu dalam strategi logistik dan pengiriman.
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
