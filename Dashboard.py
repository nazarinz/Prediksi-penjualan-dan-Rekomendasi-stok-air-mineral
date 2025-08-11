import streamlit as st
import pandas as pd
from utils import load_model, load_data, validate_dataframe, prepare_features
import time

st.set_page_config(page_title="Dashboard Prediksi Penjualan dan Rekomendasi Stok", layout="wide")

# Initialize session state
if 'dashboard_loaded' not in st.session_state:
    st.session_state.dashboard_loaded = False

# Main title
st.title("Dashboard Prediksi Penjualan dan Rekomendasi Stok")

# Data Upload Section
st.subheader("📤 Upload Data Manual")
st.markdown("Upload file CSV untuk memperbarui data yang digunakan dalam dashboard. Jika tidak upload, sistem akan menggunakan data.csv default.")

# File uploader
uploaded_file = st.file_uploader(
    "Pilih file CSV",
    type=['csv'],
    help="Upload file CSV dengan kolom: Tahun, Bulan, Nama Item, total_jumlah"
)

# Process uploaded file
if uploaded_file is not None:
    try:
        with st.spinner("Memproses file yang diupload..."):
            # Read the uploaded file
            df_uploaded = pd.read_csv(uploaded_file)
            
            # Validate the uploaded data
            validation = validate_dataframe(df_uploaded)
            
            if validation['is_valid']:
                # Show warnings if any
                for warning in validation['warnings']:
                    st.warning(warning)
                
                # Process the uploaded data
                processed_df = prepare_features(df_uploaded)
                
                if processed_df is not None:
                    # Store in session state
                    st.session_state.uploaded_df = processed_df
                    st.session_state.dashboard_loaded = False  # Reset dashboard state
                    st.session_state.data_source = "uploaded"  # Mark as uploaded data
                    
                    st.success("✅ Data berhasil diupload dan diproses!")
                    
                    # Show data summary
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Baris", len(processed_df))
                    with col2:
                        st.metric("Total Produk", processed_df['Nama Item'].nunique())
                    with col3:
                        st.metric("Rentang Periode", f"{processed_df['periode'].min().strftime('%b %Y')} - {processed_df['periode'].max().strftime('%b %Y')}")
                    
                    # Show preview of uploaded data
                    with st.expander("📋 Preview Data yang Diupload"):
                        display_cols = ['Tahun', 'Bulan', 'Nama Item', 'total_jumlah', 'periode']
                        available_cols = [col for col in display_cols if col in processed_df.columns]
                        if available_cols:
                            st.dataframe(processed_df[available_cols].head(10), use_container_width=True)
                else:
                    st.error("❌ Gagal memproses data yang diupload")
            else:
                st.error("❌ Data tidak valid:")
                for error in validation['errors']:
                    st.error(f"• {error}")
                
                st.info("""
                **Format data yang diperlukan:**
                - Kolom: `Tahun`, `Bulan`, `Nama Item`, `total_jumlah`
                - Tahun: angka (1900-2100)
                - Bulan: angka (1-12)
                - Nama Item: teks
                - total_jumlah: angka positif
                """)
                
    except Exception as e:
        st.error(f"❌ Error saat memproses file: {str(e)}")

# Data Source Information
with st.expander("ℹ️ Informasi Sumber Data"):
    if uploaded_file is not None:
        st.info("**Data saat ini:** File yang diupload")
        st.write(f"**Nama file:** {uploaded_file.name}")
        st.write(f"**Ukuran file:** {uploaded_file.size:,} bytes")
    else:
        st.info("**Data saat ini:** File data.csv (default)")
    
    st.markdown("""
    **Cara menggunakan upload data:**
    1. Siapkan file CSV dengan format yang sesuai
    2. Upload file menggunakan widget di atas
    3. Sistem akan memvalidasi dan memproses data
    4. Dashboard akan diperbarui dengan data baru
    5. Data akan tersimpan selama sesi aplikasi berjalan
    6. Jika tidak upload, sistem menggunakan data.csv default
    """)

# Loading states and error handling
try:
    # Load model with loading state
    with st.spinner("Memuat model..."):
        model = load_model()
        if model is not None:
            st.success("✅ Model berhasil dimuat")
        else:
            st.error("❌ Model tidak dapat dimuat")
    
    # Load data with loading state
    if "uploaded_df" not in st.session_state:
        with st.spinner("Memuat data..."):
            st.session_state.uploaded_df = load_data()
            st.session_state.data_source = "default"  # Mark as default data
    
    # Check if data is loaded successfully
    if st.session_state.uploaded_df is not None:
        df = st.session_state.uploaded_df
        
        # Show success message only once
        if not st.session_state.dashboard_loaded:
            st.success("✅ Dashboard siap digunakan!")
            st.session_state.dashboard_loaded = True
        
        # Metrics Row with validation
        st.subheader("📊 Metrik Utama")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            try:
                total_products = df['Nama Item'].nunique()
                st.metric("Total Produk", f"{total_products:,}")
            except Exception as e:
                st.error("Error menghitung total produk")
        
        with col2:
            try:
                total_sales = df['total_jumlah'].sum()
                st.metric("Total Penjualan", f"{total_sales:,}")
            except Exception as e:
                st.error("Error menghitung total penjualan")
        
        with col3:
            try:
                avg_sales = df['total_jumlah'].mean()
                st.metric("Rata-rata Penjualan", f"{avg_sales:,.0f}")
            except Exception as e:
                st.error("Error menghitung rata-rata penjualan")
        
        with col4:
            try:
                total_periods = df['periode'].nunique()
                st.metric("Total Periode", f"{total_periods}")
            except Exception as e:
                st.error("Error menghitung total periode")
        
        # Top 10 Products by Sales with loading state
        st.subheader("📊 10 Produk Teratas Berdasarkan Penjualan")
        
        with st.spinner("Menghitung produk teratas..."):
            try:
                top_products = df.groupby('Nama Item')['total_jumlah'].sum().sort_values(ascending=False).head(10)
                
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    # Bar chart for top 10 products
                    import plotly.express as px
                    fig = px.bar(
                        x=top_products.values,
                        y=top_products.index,
                        orientation='h',
                        title="10 Produk Teratas",
                        labels={'x': 'Total Penjualan', 'y': 'Nama Produk'}
                    )
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    # Table for top 10 products
                    top_products_df = pd.DataFrame({
                        'Nama Produk': top_products.index,
                        'Total Penjualan': top_products.values
                    }).reset_index(drop=True)
                    top_products_df.index = top_products_df.index + 1
                    st.dataframe(top_products_df, use_container_width=True)
                    
            except Exception as e:
                st.error(f"Error menghitung produk teratas: {str(e)}")
        
        # Data Preview with validation
        st.subheader("📋 Preview Data")
        try:
            display_cols = ['Tahun', 'Bulan', 'Nama Item', 'total_jumlah', 'periode']
            available_cols = [col for col in display_cols if col in df.columns]
            
            if available_cols:
                st.write("**Data Setelah Diproses (5 baris pertama):**")
                st.dataframe(df[available_cols].head(), use_container_width=True)
            else:
                st.warning("Kolom yang diperlukan tidak tersedia untuk preview")
                
        except Exception as e:
            st.error(f"Error menampilkan preview data: {str(e)}")
        
        # Additional Statistics with error handling
        st.subheader("📈 Statistik Tambahan")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            try:
                st.write("**Rentang Periode:**")
                period_range = f"{df['periode'].min().strftime('%b %Y')} - {df['periode'].max().strftime('%b %Y')}"
                st.info(period_range)
            except Exception as e:
                st.error("Error menghitung rentang periode")
        
        with col2:
            try:
                st.write("**Distribusi Penjualan:**")
                sales_stats = df['total_jumlah'].describe()
                st.write(f"Min: {sales_stats['min']:,.0f}")
                st.write(f"Max: {sales_stats['max']:,.0f}")
                st.write(f"Std: {sales_stats['std']:,.0f}")
            except Exception as e:
                st.error("Error menghitung distribusi penjualan")
        
        with col3:
            st.write("**Status Model:**")
            if model is not None:
                st.success("✅ Model siap digunakan")
            else:
                st.error("❌ Model tidak tersedia")
        
        # Data Quality Check with comprehensive validation
        st.subheader("🔍 Pemeriksaan Kualitas Data")
        col1, col2 = st.columns(2)
        
        with col1:
            try:
                st.write("**Missing Values:**")
                missing_data = df.isnull().sum()
                if missing_data.sum() == 0:
                    st.success("✅ Tidak ada missing values")
                else:
                    st.warning(f"⚠️ Ada {missing_data.sum()} missing values")
                    st.dataframe(missing_data[missing_data > 0])
            except Exception as e:
                st.error("Error memeriksa missing values")
        
        with col2:
            try:
                st.write("**Data Types:**")
                # Convert dtypes to string to avoid Arrow serialization issues
                dtype_df = df.dtypes.to_frame('Data Type')
                dtype_df['Data Type'] = dtype_df['Data Type'].astype(str)
                # Convert to regular pandas DataFrame to avoid Arrow issues
                dtype_df = pd.DataFrame(dtype_df)
                st.dataframe(dtype_df, use_container_width=True)
            except Exception as e:
                st.error("Error memeriksa tipe data")
                st.write("Tipe data tidak dapat ditampilkan karena masalah kompatibilitas")
        
        # Data validation summary
        st.subheader("✅ Validasi Data")
        validation_status = []
        
        try:
            # Check data completeness
            if not df.empty:
                validation_status.append("✅ Data tidak kosong")
            else:
                validation_status.append("❌ Data kosong")
            
            # Check required columns
            required_cols = ['Tahun', 'Bulan', 'Nama Item', 'total_jumlah']
            missing_cols = [col for col in required_cols if col not in df.columns]
            if not missing_cols:
                validation_status.append("✅ Semua kolom required tersedia")
            else:
                validation_status.append(f"❌ Kolom yang hilang: {missing_cols}")
            
            # Check data ranges
            if 'Tahun' in df.columns and 'Bulan' in df.columns:
                if df['Tahun'].min() >= 1900 and df['Tahun'].max() <= 2100:
                    validation_status.append("✅ Range tahun valid")
                else:
                    validation_status.append("⚠️ Range tahun di luar batas wajar")
                
                if df['Bulan'].min() >= 1 and df['Bulan'].max() <= 12:
                    validation_status.append("✅ Range bulan valid")
                else:
                    validation_status.append("❌ Range bulan tidak valid")
            
            # Check for negative sales
            if 'total_jumlah' in df.columns:
                if (df['total_jumlah'] < 0).any():
                    validation_status.append("⚠️ Ada nilai penjualan negatif")
                else:
                    validation_status.append("✅ Semua nilai penjualan positif")
            
            # Display validation results
            for status in validation_status:
                if status.startswith("✅"):
                    st.success(status)
                elif status.startswith("⚠️"):
                    st.warning(status)
                else:
                    st.error(status)
                    
        except Exception as e:
            st.error(f"Error dalam validasi data: {str(e)}")

    else:
        st.error("❌ Data tidak berhasil dimuat. Pastikan file 'data.csv' ada di direktori yang sama.")
        
        st.info("""
        **Format data yang diperlukan:**
        - Kolom: `Tahun`, `Bulan`, `Nama Item`, `total_jumlah`
        - Format: CSV
        - Encoding: UTF-8
        - Pastikan file tidak kosong dan dapat dibaca
        """)
        
        # Add troubleshooting tips
        st.subheader("🔧 Troubleshooting")
        st.markdown("""
        1. **Periksa file data.csv** ada di folder yang sama dengan aplikasi
        2. **Pastikan format CSV** benar dan tidak rusak
        3. **Cek encoding file** (gunakan UTF-8)
        4. **Validasi kolom** sesuai dengan yang diperlukan
        5. **Restart aplikasi** jika masih bermasalah
        6. **Upload data manual** menggunakan fitur upload di atas
        """)

except Exception as e:
    st.error(f"❌ Error tidak terduga: {str(e)}")
    st.error("Silakan refresh halaman atau restart aplikasi")
    
    # Add error details for debugging
    with st.expander("🔍 Detail Error (untuk debugging)"):
        st.code(f"""
        Error Type: {type(e).__name__}
        Error Message: {str(e)}
        Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}
        """)