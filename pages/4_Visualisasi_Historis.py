import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.title("Visualisasi Tren Historis Penjualan")

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

df = st.session_state.get("uploaded_df", None)

if df is not None:
    items = df['Nama Item'].unique()
    selected_items = st.multiselect("Pilih Nama Item", items, default=items[:3])
    if selected_items:
        min_date = df['periode'].min()
        max_date = df['periode'].max()
        date_range = st.date_input(
            "Pilih rentang waktu",
            value=[min_date, max_date],
            min_value=min_date,
            max_value=max_date
        )
        if len(date_range) == 2:
            start_date, end_date = date_range
            mask = (df['periode'] >= pd.to_datetime(start_date)) & (df['periode'] <= pd.to_datetime(end_date))
            filtered_df = df[mask & df['Nama Item'].isin(selected_items)]
            if not filtered_df.empty:
                fig = go.Figure()
                for item in selected_items:
                    item_data = filtered_df[filtered_df['Nama Item'] == item].sort_values('periode')
                    # Data aktual
                    fig.add_trace(go.Scatter(
                        x=item_data['periode'], y=item_data['total_jumlah'],
                        mode='lines+markers',
                        name=f'{item} - Aktual',
                        marker=dict(symbol='circle', size=8),
                        line=dict(width=2),
                        hovertemplate='Periode: %{x|%b %Y}<br>Aktual: %{y}<extra></extra>'
                    ))
                    # Prediksi jika ada
                    if 'prediksi_jumlah' in item_data.columns:
                        fig.add_trace(go.Scatter(
                            x=item_data['periode'], y=item_data['prediksi_jumlah'],
                            mode='lines+markers',
                            name=f'{item} - Prediksi',
                            marker=dict(symbol='square', size=8),
                            line=dict(dash='dash', width=2),
                            hovertemplate='Periode: %{x|%b %Y}<br>Prediksi: %{y}<extra></extra>'
                        ))
                fig.update_layout(
                    title="Tren Penjualan Historis",
                    xaxis_title="Periode",
                    yaxis_title="Jumlah Penjualan",
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    hovermode="x unified",
                    margin=dict(l=40, r=40, t=60, b=40),
                    template="plotly_white"
                )
                fig.update_xaxes(tickformat="%b %Y", tickangle=45)
                st.plotly_chart(fig, use_container_width=True)
                st.subheader("Statistik Deskriptif")
                stats = filtered_df.groupby('Nama Item')['total_jumlah'].agg([
                    'count', 'mean', 'std', 'min', 'max'
                ]).round(2)
                stats.columns = ['Jumlah Data', 'Rata-rata', 'Std Dev', 'Minimum', 'Maksimum']
                st.dataframe(stats)
            else:
                st.warning("Tidak ada data untuk rentang waktu dan item yang dipilih.")
    else:
        st.warning("Pilih minimal satu item untuk divisualisasikan.")
else:
    st.warning("Data belum dimuat. Periksa file `data.csv` atau upload data manual di Dashboard.")
