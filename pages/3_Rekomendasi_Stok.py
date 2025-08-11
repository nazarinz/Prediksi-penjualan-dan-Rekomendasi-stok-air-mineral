import streamlit as st
import pandas as pd
from io import BytesIO

st.title("Rekomendasi Stok Bulan Berikutnya")

# Data Source Information
with st.expander("ℹ️ Informasi Sumber Data"):
    if st.session_state.get("data_source") == "uploaded":
        st.info("**Data saat ini:** File yang diupload di Dashboard")
    else:
        st.info("**Data saat ini:** File data.csv (default)")
    
    st.markdown("""
    **Cara mengubah data:**
    1. Kembali ke halaman Dashboard
    2. Upload file CSV menggunakan widget upload
    3. Sistem akan memvalidasi dan memproses data
    4. Data akan tersimpan dan dapat digunakan di semua halaman
    """)

if "future_df" in st.session_state and st.session_state.future_df is not None:
    future_df = st.session_state.future_df.copy()
    items = future_df['Nama Item'].unique()
    selected_item = st.selectbox("Pilih Nama Item", items, key="rekom_item")
    filtered_df = future_df[future_df['Nama Item'] == selected_item].copy()
    stok_saat_ini = st.number_input(
        f"Masukkan stok saat ini untuk {selected_item}",
        min_value=0, value=0, step=1, key=f"stok_input_{selected_item}"
    )
    
    # Safety Stock Factor Section with Explanation
    st.subheader("🛡️ Safety Stock Factor")
    safety_factor = st.slider("Safety Stock Factor", 1.0, 2.0, 1.1, 0.1)
    
    # Explanation of Safety Stock Factor
    with st.expander("📖 Penjelasan Safety Stock Factor"):
        st.markdown("""
        ### Apa itu Safety Stock Factor?
        Safety Stock Factor adalah pengali untuk menentukan jumlah stok pengaman yang diperlukan untuk mengantisipasi ketidakpastian dalam permintaan.
        
        ### Rumus Perhitungan:
        
        **1. Safety Stock = Prediksi × (Safety Factor - 1)**
        ```
        Safety Stock = Prediksi × (1.1 - 1) = Prediksi × 0.1
        ```
        
        **2. Rekomendasi Stok = (Prediksi × Safety Factor) - Stok Saat Ini**
        ```
        Rekomendasi Stok = (Prediksi × 1.1) - Stok Saat Ini
        ```
        
        ### Contoh Perhitungan:
        - **Prediksi**: 1000 unit
        - **Safety Factor**: 1.1 (10% buffer)
        - **Stok Saat Ini**: 50 unit
        
        **Safety Stock** = 1000 × (1.1 - 1) = 1000 × 0.1 = **100 unit**
        
        **Rekomendasi Stok** = (1000 × 1.1) - 50 = 1100 - 50 = **1050 unit**
        
        ### Rekomendasi Safety Factor:
        - **1.0**: Tanpa safety stock (berisiko)
        - **1.1**: Safety stock 10% (moderat)
        - **1.2**: Safety stock 20% (aman)
        - **1.5**: Safety stock 50% (sangat aman)
        - **2.0**: Safety stock 100% (terlalu konservatif)
        """)
    
    filtered_df['stok_saat_ini'] = stok_saat_ini
    filtered_df['rekomendasi_stok'] = (filtered_df['prediksi_jumlah'] * safety_factor - stok_saat_ini).clip(lower=0).round().astype(int)
    filtered_df['safety_stock'] = (filtered_df['prediksi_jumlah'] * (safety_factor - 1)).round().astype(int)
    
    st.markdown("### Rekomendasi Stok untuk Item Terpilih")
    display_cols = ['Nama Item', 'periode', 'prediksi_jumlah', 'stok_saat_ini', 'rekomendasi_stok', 'safety_stock']
    st.dataframe(filtered_df[display_cols])
    
    st.markdown("### Ringkasan")
    total_prediksi = filtered_df['prediksi_jumlah'].sum()
    total_rekomendasi = filtered_df['rekomendasi_stok'].sum()
    total_safety = filtered_df['safety_stock'].sum()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Prediksi (3 Bulan)", f"{total_prediksi:.0f}")
    with col2:
        st.metric("Stok Saat Ini", f"{stok_saat_ini}")
    with col3:
        st.metric("Total Rekomendasi Stok", f"{total_rekomendasi}")
    with col4:
        st.metric("Total Safety Stock", f"{total_safety}")
    
    # Rincian per Bulan dengan tampilan horizontal yang rapi
    st.markdown("#### 📅 Rincian per Bulan")
    
    # Sort by period
    sorted_df = filtered_df.sort_values("periode")
    
    # Create horizontal layout for monthly details
    for i, (_, row) in enumerate(sorted_df.iterrows()):
        bulan_str = row["periode"].strftime("%B %Y")
        
        # Create a container for each month
        with st.container():
            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
            
            with col1:
                st.markdown(f"**{bulan_str}**")
            
            with col2:
                # Create a styled box for Prediksi
                st.markdown("""
                <div style="
                    background-color: #e8f4fd;
                    border: 1px solid #2196F3;
                    border-radius: 5px;
                    padding: 10px;
                    text-align: center;
                    margin: 5px 0;
                ">
                    <strong style="color: #1976D2;">Prediksi</strong><br>
                    <span style="font-size: 18px; font-weight: bold; color: #1976D2;">{}</span>
                </div>
                """.format(int(row['prediksi_jumlah'])), unsafe_allow_html=True)
            
            with col3:
                # Create a styled box for Rekomendasi Stok
                st.markdown("""
                <div style="
                    background-color: #e8f5e8;
                    border: 1px solid #4CAF50;
                    border-radius: 5px;
                    padding: 10px;
                    text-align: center;
                    margin: 5px 0;
                ">
                    <strong style="color: #2E7D32;">Rekomendasi Stok</strong><br>
                    <span style="font-size: 18px; font-weight: bold; color: #2E7D32;">{}</span>
                </div>
                """.format(int(row['rekomendasi_stok'])), unsafe_allow_html=True)
            
            with col4:
                # Create a styled box for Safety Stock
                st.markdown("""
                <div style="
                    background-color: #fff3e0;
                    border: 1px solid #FF9800;
                    border-radius: 5px;
                    padding: 10px;
                    text-align: center;
                    margin: 5px 0;
                ">
                    <strong style="color: #E65100;">Safety Stock</strong><br>
                    <span style="font-size: 18px; font-weight: bold; color: #E65100;">{}</span>
                </div>
                """.format(int(row['safety_stock'])), unsafe_allow_html=True)
        
        # Add separator between months
        if i < len(sorted_df) - 1:
            st.markdown("---")
    
    # Download button
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        filtered_df.to_excel(writer, sheet_name='Rekomendasi Item', index=False)
    st.download_button(
        label="Download Rekomendasi Stok (Excel)",
        data=output.getvalue(),
        file_name=f"rekomendasi_stok_{selected_item}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
elif "predictions_df" in st.session_state and st.session_state.predictions_df is not None:
    st.info("Silakan lakukan prediksi 3 bulan kedepan terlebih dahulu di menu 'Prediksi Penjualan'.")
else:
    st.warning("Silakan upload data dan lakukan prediksi terlebih dahulu.")
