import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import folium
from folium.plugins import HeatMap
from streamlit_folium import folium_static

customer_df = pd.read_csv("customer_dataset.csv")
geolocation_df = pd.read_csv("geolocation_dataset.csv")
order_df = pd.read_csv("order_dataset.csv")
order_items_df = pd.read_csv("order_items_dataset.csv")
order_payments_df = pd.read_csv("order_payments_dataset.csv")
product_df = pd.read_csv("product_dataset.csv")
seller_df = pd.read_csv("seller_dataset.csv")

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

st.set_page_config(page_title="E-Commerce Data Analysis", layout="wide")
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

# =========== PAGE 1: SALE TREND ===========
if page == "Sale Trend":
    st.header("Pertanyaan 1: Bagaimana trend penjualan di E-commerce di rentang tanggal tertentu?")
    st.header("Visualisasi: Tren Penjualan")
    merged_orders = pd.merge(order_df, order_items_df, on="order_id", how="inner")
    merged_orders["order_delivered_customer_date"] = pd.to_datetime(
        merged_orders["order_delivered_customer_date"]
    )

    st.subheader("Visualisasi: Jumlah Item Terjual per Hari (Filter by Date Range)")
    min_date = merged_orders["order_delivered_customer_date"].min().date()
    max_date = merged_orders["order_delivered_customer_date"].max().date()
    selected_date_range = st.date_input(
        "Pilih rentang tanggal untuk melihat jumlah item terjual per hari:",
        [min_date, max_date]  # default range
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
            range_data = merged_orders[mask].copy()

            if range_data.empty:
                st.info("Tidak ada pesanan di rentang tanggal yang dipilih.")
            else:
                daily_item_count = (
                    range_data
                    .groupby(range_data["order_delivered_customer_date"].dt.date)["order_item_id"]
                    .count()  # total item per tanggal
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

# =========== PAGE 2: LATE ORDERS ANALYSIS ===========
elif page == "Late Orders Analysis":
    st.header("Pertanyaan 2: Berapa persentase pesanan yang terlambat sampai ke pelanggan?")
    
    order_df['order_estimated_delivery_date'] = pd.to_datetime(order_df['order_estimated_delivery_date'])
    order_df['order_delivered_customer_date'] = pd.to_datetime(order_df['order_delivered_customer_date'])
    
    delivered_orders = order_df[order_df['order_status'] == 'delivered'].copy()

    delivered_orders['late_delivery'] = (
        delivered_orders['order_delivered_customer_date'] 
        > delivered_orders['order_estimated_delivery_date']
    )
    late_percentage = delivered_orders['late_delivery'].mean() * 100

    st.subheader("Visualisasi 1: Pie Chart On-Time vs Late")
    labels = ['On Time', 'Late']
    sizes = [100 - late_percentage, late_percentage]
    colors = ['#4CAF50', '#F44336']
    explode = (0.1, 0)
    fig, ax = plt.subplots(figsize=(4,4))
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
        - Mayoritas pesanan (sekitar {100 - late_percentage:.1f}%) dikirim tepat waktu.
        - Faktor keterlambatan yang tersisa (sekitar {late_percentage:.1f}%) bisa disebabkan 
          oleh jarak pengiriman, logistik, maupun adanya lonjakan pembelian yang terlalu tinggi sehingga kurang adanya persiapan.
        """
    )

    # --- Visualization 2: Time Series ---
    st.subheader("Visualisasi 2: Time Series Keterlambatan Pengiriman")
    orders_by_date = delivered_orders.groupby(
        delivered_orders['order_delivered_customer_date'].dt.date
    ).size()

    late_orders_by_date = delivered_orders[
        delivered_orders['late_delivery']
    ].groupby(
        delivered_orders['order_delivered_customer_date'].dt.date
    ).size()
    
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
    st.pyplot(fig)

    st.markdown("**Insight (Time Series):**")
    st.markdown(
        """
        - Bisa diketahui bahwa setiap adanya peningkatan pembelian, maka setelahnya akan diikuti semakin banyaknya barang terlamabt
        - Kemudian, setelah adanya peningkatan jumlah barang terlambat, akan menyebabnya pembelian di E-commerce tersebut menurun. Hal ini bisa dikarenakan menurunnya kepercayaan pada platform E-commerce tersebut
        """
    )

# =========== PAGE 3: PAYMENT METHOD ANALYSIS ===========
elif page == "Payment Method Analysis":
    st.header("Pertanyaan 3: Metode pembayaran mana yang paling banyak digunakan dan mana yang paling jarang digunakan?")

    payment_counts = order_payments_df['payment_type'].value_counts()

    # --- Visualization: Pie Chart ---
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
        - Metode pembayaran yang paling banyak digunakan adalah Credit Card.
        - Boleto juga menempati posisi yang cukup signifikan.
        - Metode lain seperti Voucher dan Debit Card memiliki proporsi yang lebih kecil.
        - Mengadakan campaign atau program voucher atau kupon untuk pengguna credit card bisa meningkatkan penjualan karena banyaknya orang yang menggunakan metode pembayaran tersebut
        """
    )

# =========== PAGE 4: CITY-WISE DISTRIBUTION ===========
elif page == "City-wise Distribution":
    st.header("Pertanyaan 4: Kota mana yang memiliki jumlah pelanggan terbanyak dan kota mana yang memiliki jumlah penjual terbanyak?")

    # --- Visualization 1: Bar Chart Top 10 Cities (Customers) ---
    st.subheader("Visualisasi 1: Top 10 Cities with Most Customers")

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

    # Developer's Insight (Top 10 Cities - Customers)
    st.markdown("**Insight (Top 10 Cities - Customers):**")
    st.markdown(
        """
        - Kota dengan jumlah pelanggan terbanyak biasanya kota besar atau 
        pusat bisnis, seperti São Paulo atau Rio de Janeiro.
        - Distribusi pelanggan umumnya terpusat di wilayah tenggara Brasil.
        """
    )
    # --- Visualization 2 & 3: Heatmaps (Customer & Seller Density) ---
    st.subheader("Visualisasi 2: Heatmap Customer & Seller")
    customer_counts_geo = customer_geo.groupby(["geolocation_lat", "geolocation_lng"]).size().reset_index(name="customer_count")
    seller_counts_geo = seller_geo.groupby(["geolocation_lat", "geolocation_lng"]).size().reset_index(name="seller_count")

    customer_map = folium.Map(location=[-2.5489, -46.633], zoom_start=5)
    seller_map = folium.Map(location=[-2.5489, -46.633], zoom_start=5)
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

    # Heatmap 1 (Customers)
    HeatMap(
        heat_data_customers,
        name="Customer Density",
        radius=15
    ).add_to(customer_map)

    # Heatmap 2 (Sellers)
    HeatMap(
        heat_data_sellers, 
        name="Seller Density", 
        radius=15
    ).add_to(seller_map)

    st.markdown("**Customer Density Map**")
    folium_static(customer_map)

    st.markdown("**Seller Density Map**")
    folium_static(seller_map)
    st.markdown("**Insight (Heatmaps):**")
    st.markdown(
        """
        - Peta kepadatan pelanggan dan penjual memperlihatkan konsentrasi tertinggi 
          di area perkotaan padat penduduk.
        - Dengan mengetahui lokasi penjual dan pelanggan, dapat dioptimalkan 
          strategi pengiriman dan penyebaran gudang,, terutama di daerah dengan pembeli yang banyak dari luar ameriak selatan.
        - Adanya pembeli dari luar amerika selatan, membuka peluang untuk expansi ke luar amerika selatan, seperti eropa, atau Amerika Serikat.
        """
    )
