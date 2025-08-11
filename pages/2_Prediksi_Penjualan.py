import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from io import BytesIO
from utils import load_model, load_data, predict_future
import time

st.title("Prediksi Jumlah Penjualan")

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

# Initialize session state
if 'prediction_loaded' not in st.session_state:
    st.session_state.prediction_loaded = False

# Load model with loading state
try:
    with st.spinner("Memuat model..."):
        model = load_model()
        if model is None:
            st.error("❌ Model tidak dapat dimuat. Pastikan file 'best_model.joblib' tersedia.")
            st.stop()
        else:
            st.success("✅ Model berhasil dimuat")

    # Load data with loading state
    if "uploaded_df" not in st.session_state:
        with st.spinner("Memuat data..."):
            st.session_state.uploaded_df = load_data()
            st.session_state.data_source = "default"  # Mark as default data
    
    if "predictions_df" not in st.session_state:
        st.session_state.predictions_df = None
    if "future_df" not in st.session_state:
        st.session_state.future_df = None

    df = st.session_state.uploaded_df

    if df is not None and model is not None:
        # Show success message only once
        if not st.session_state.prediction_loaded:
            st.success("✅ Halaman prediksi siap digunakan!")
            st.session_state.prediction_loaded = True
        
        # Data validation
        st.subheader("🔍 Validasi Data")
        try:
            feature_cols = ['Tahun', 'Bulan', 'quarter', 'is_start_year', 'is_end_year',
                            'lag_1', 'lag_2', 'lag_3', 'ma_3', 'ma_6', 'diff_1']
            
            missing_features = [col for col in feature_cols if col not in df.columns]
            if missing_features:
                st.error(f"❌ Fitur yang diperlukan tidak ditemukan: {missing_features}")
                st.stop()
            
            df_clean = df.dropna()
            if len(df_clean) == 0:
                st.error("❌ Tidak ada data yang dapat digunakan untuk prediksi (semua data mengandung NaN)")
                st.stop()
            
            st.success(f"✅ Data valid: {len(df_clean)} baris data tersedia untuk prediksi")
            
        except Exception as e:
            st.error(f"❌ Error dalam validasi data: {str(e)}")
            st.stop()
        
        # Prediction section
        st.subheader("📊 Prediksi Penjualan")
        
        try:
            with st.spinner("Melakukan prediksi..."):
                X = df_clean[feature_cols].fillna(0)
                predictions = model.predict(X)
                df_clean = df_clean.copy()
                df_clean['prediksi_jumlah'] = predictions
                st.session_state.predictions_df = df_clean
                
                st.success("✅ Prediksi berhasil dilakukan!")
                
                # Display results
                st.write("**Hasil Prediksi:**")
                display_cols = ['Tahun', 'Bulan', 'Nama Item', 'total_jumlah', 'prediksi_jumlah']
                available_cols = [col for col in display_cols if col in df_clean.columns]
                st.dataframe(df_clean[available_cols])
                
                # Calculate metrics with error handling
                try:
                    mae = np.mean(np.abs(df_clean['total_jumlah'] - df_clean['prediksi_jumlah']))
                    mse = np.mean((df_clean['total_jumlah'] - df_clean['prediksi_jumlah']) ** 2)
                    rmse = np.sqrt(mse)
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("MAE", f"{mae:.2f}")
                    with col2:
                        st.metric("MSE", f"{mse:.2f}")
                    with col3:
                        st.metric("RMSE", f"{rmse:.2f}")
                        
                except Exception as e:
                    st.error(f"❌ Error menghitung metrik evaluasi: {str(e)}")
                
        except Exception as e:
            st.error(f"❌ Error dalam prediksi: {str(e)}")
            st.write("Pastikan data memiliki format yang benar dan model sudah dimuat.")
            st.stop()
        
        # Future prediction section
        st.subheader("🔮 Prediksi 3 Bulan Kedepan")
        
        try:
            with st.spinner("Memperkirakan 3 bulan ke depan..."):
                future_df = predict_future(df_clean, model, months=3)
                
                if future_df is not None:
                    st.session_state.future_df = future_df
                    st.success("✅ Prediksi 3 bulan ke depan berhasil dibuat!")
                    
                    # Display future predictions
                    future_display_cols = ['Nama Item', 'periode', 'prediksi_jumlah', 'CI_lower', 'CI_upper']
                    available_future_cols = [col for col in future_display_cols if col in future_df.columns]
                    st.dataframe(future_df[available_future_cols])
                    
                    # Visualization section
                    st.subheader("📈 Visualisasi Prediksi (Interaktif)")
                    
                    try:
                        items = df_clean['Nama Item'].unique()
                        if len(items) > 0:
                            selected_item = st.selectbox("Pilih Nama Item", items, key="prediksi_item")
                            
                            with st.spinner("Membuat visualisasi..."):
                                hist_data = df_clean[df_clean['Nama Item'] == selected_item].copy().sort_values('periode')
                                future_item = future_df[future_df['Nama Item'] == selected_item]
                                
                                # Create Plotly figure
                                fig = go.Figure()
                                
                                # Historical actual data
                                fig.add_trace(go.Scatter(
                                    x=hist_data['periode'], y=hist_data['total_jumlah'],
                                    mode='lines+markers+text',
                                    name='Data Aktual',
                                    marker=dict(color='#1976d2'),
                                    line=dict(color='#1976d2'),
                                    text=[f"{int(y)}" for y in hist_data['total_jumlah']],
                                    textposition="top center",
                                    hovertemplate='Periode: %{x|%b %Y}<br>Aktual: %{y}<extra></extra>'
                                ))
                                
                                # Historical predictions
                                fig.add_trace(go.Scatter(
                                    x=hist_data['periode'], y=hist_data['prediksi_jumlah'],
                                    mode='lines+markers+text',
                                    name='Prediksi Model',
                                    marker=dict(color='#ff9800', symbol='square'),
                                    line=dict(color='#ff9800', dash='dash'),
                                    text=[f"{int(y)}" for y in hist_data['prediksi_jumlah']],
                                    textposition="bottom center",
                                    hovertemplate='Periode: %{x|%b %Y}<br>Prediksi Model: %{y}<extra></extra>'
                                ))
                                
                                # Future predictions
                                if not future_item.empty:
                                    fig.add_trace(go.Scatter(
                                        x=future_item['periode'], y=future_item['prediksi_jumlah'],
                                        mode='lines+markers+text',
                                        name='Prediksi 3 Bulan',
                                        marker=dict(color='#d32f2f', symbol='diamond'),
                                        line=dict(color='#d32f2f', width=3),
                                        text=[f"{int(y)}" for y in future_item['prediksi_jumlah']],
                                        textposition="bottom center",
                                        hovertemplate='Periode: %{x|%b %Y}<br>Prediksi 3 Bulan: %{y}<extra></extra>'
                                    ))
                                    
                                    # Confidence interval
                                    fig.add_trace(go.Scatter(
                                        x=pd.concat([future_item['periode'], future_item['periode'][::-1]]),
                                        y=pd.concat([future_item['CI_upper'], future_item['CI_lower'][::-1]]),
                                        fill='toself',
                                        fillcolor='rgba(211,47,47,0.18)',
                                        line=dict(color='rgba(255,255,255,0)'),
                                        hoverinfo='skip',
                                        showlegend=True,
                                        name='95% Confidence Interval',
                                    ))
                                    
                                    # CI labels
                                    fig.add_trace(go.Scatter(
                                        x=future_item['periode'], y=future_item['CI_upper'],
                                        mode='text',
                                        text=[f"{int(y)}" for y in future_item['CI_upper']],
                                        textposition="top right",
                                        showlegend=False,
                                        hoverinfo='skip',
                                        textfont=dict(color='#b71c1c', size=10)
                                    ))
                                    
                                    fig.add_trace(go.Scatter(
                                        x=future_item['periode'], y=future_item['CI_lower'],
                                        mode='text',
                                        text=[f"{int(y)}" for y in future_item['CI_lower']],
                                        textposition="bottom left",
                                        showlegend=False,
                                        hoverinfo='skip',
                                        textfont=dict(color='#b71c1c', size=10)
                                    ))
                                
                                # Update layout
                                fig.update_layout(
                                    title=f"Prediksi Penjualan - {selected_item}",
                                    xaxis_title="Periode",
                                    yaxis_title="Jumlah",
                                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                                    hovermode="x unified",
                                    margin=dict(l=40, r=40, t=60, b=40),
                                    template="plotly_white"
                                )
                                fig.update_xaxes(tickformat="%b %Y", tickangle=45)
                                st.plotly_chart(fig, use_container_width=True)
                                
                        else:
                            st.warning("⚠️ Tidak ada item yang tersedia untuk visualisasi")
                            
                    except Exception as e:
                        st.error(f"❌ Error dalam visualisasi: {str(e)}")
                    
                    # Export section
                    st.subheader("📥 Export Hasil")
                    try:
                        with st.spinner("Menyiapkan file export..."):
                            output = BytesIO()
                            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                                df_clean[display_cols].to_excel(writer, sheet_name='Prediksi Current', index=False)
                                future_df.to_excel(writer, sheet_name='Prediksi 3 Bulan', index=False)
                            
                            st.download_button(
                                label="📥 Download Hasil Prediksi (Excel)",
                                data=output.getvalue(),
                                file_name=f"prediksi_penjualan_{time.strftime('%Y%m%d_%H%M%S')}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
                            st.success("✅ File export siap diunduh")
                            
                    except Exception as e:
                        st.error(f"❌ Error dalam export: {str(e)}")
                        
                else:
                    st.error("❌ Gagal membuat prediksi 3 bulan kedepan")
                    
        except Exception as e:
            st.error(f"❌ Error dalam prediksi masa depan: {str(e)}")
            
    elif model is None:
        st.error("❌ Model tidak tersedia. Pastikan file model sudah dimuat.")
    else:
        st.warning("⚠️ Data belum dimuat. Periksa file `data.csv`.")

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
