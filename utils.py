import streamlit as st
import pandas as pd
import numpy as np
import joblib
import logging
from typing import Optional, Dict, Any
import warnings
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@st.cache_resource
def load_model():
    """
    Load the trained model with robust error handling.
    
    Returns:
        model: Trained model or None if error
    """
    try:
        model = joblib.load("best_model.joblib")
        logger.info("Model loaded successfully")
        return model
    except FileNotFoundError:
        error_msg = "Model file 'best_model.joblib' tidak ditemukan. Pastikan file model ada di direktori yang sama."
        st.error(error_msg)
        logger.error("Model file not found")
        return None
    except Exception as e:
        error_msg = f"Error saat memuat model: {str(e)}"
        st.error(error_msg)
        logger.error(f"Model loading error: {str(e)}")
        return None

def validate_dataframe(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Validate input dataframe for required columns and data types.
    
    Args:
        df: Input dataframe
        
    Returns:
        dict: Validation results with status and errors
    """
    validation_result = {
        'is_valid': True,
        'errors': [],
        'warnings': []
    }
    
    # Check required columns
    required_cols = ['Tahun', 'Bulan', 'Nama Item', 'total_jumlah']
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        validation_result['is_valid'] = False
        validation_result['errors'].append(f"Kolom yang diperlukan tidak ditemukan: {missing_cols}")
        return validation_result
    
    # Check data types
    try:
        df['Tahun'] = pd.to_numeric(df['Tahun'], errors='coerce')
        df['Bulan'] = pd.to_numeric(df['Bulan'], errors='coerce')
        df['total_jumlah'] = pd.to_numeric(df['total_jumlah'], errors='coerce')
    except Exception as e:
        validation_result['is_valid'] = False
        validation_result['errors'].append(f"Error konversi tipe data: {str(e)}")
        return validation_result
    
    # Check for missing values
    missing_data = df[required_cols].isnull().sum()
    if missing_data.sum() > 0:
        validation_result['warnings'].append(f"Ada {missing_data.sum()} missing values dalam data")
    
    # Check data ranges
    if df['Tahun'].min() < 1900 or df['Tahun'].max() > 2100:
        validation_result['warnings'].append("Tahun di luar range yang wajar (1900-2100)")
    
    if df['Bulan'].min() < 1 or df['Bulan'].max() > 12:
        validation_result['is_valid'] = False
        validation_result['errors'].append("Bulan harus antara 1-12")
    
    if (df['total_jumlah'] < 0).any():
        validation_result['warnings'].append("Ada nilai penjualan negatif")
    
    # Check for empty dataframe
    if df.empty:
        validation_result['is_valid'] = False
        validation_result['errors'].append("Dataframe kosong")
    
    return validation_result

@st.cache_data
def prepare_features(df: pd.DataFrame) -> Optional[pd.DataFrame]:
    """
    Prepare features for model prediction with robust error handling.
    
    Args:
        df: Input dataframe
        
    Returns:
        pd.DataFrame: Processed dataframe or None if error
    """
    try:
        # Show loading state
        with st.spinner("Memproses data..."):
            df = df.copy()
            
            # Validate input data
            validation = validate_dataframe(df)
            if not validation['is_valid']:
                for error in validation['errors']:
                    st.error(error)
                logger.error(f"Data validation failed: {validation['errors']}")
                return None
            
            # Show warnings if any
            for warning in validation['warnings']:
                st.warning(warning)
            
            # Create period column
            try:
                df['periode'] = pd.to_datetime(df['Tahun'].astype(str) + '-' + df['Bulan'].astype(str) + '-01')
            except Exception as e:
                st.error(f"Error saat membuat kolom 'periode': {str(e)}")
                logger.error(f"Period creation error: {str(e)}")
                return None
            
            # Sort and create features
            df = df.sort_values(['Nama Item', 'periode'])
            df['quarter'] = df['Bulan'].apply(lambda x: (x - 1) // 3 + 1)
            df['is_start_year'] = (df['Bulan'] == 1).astype(int)
            df['is_end_year'] = (df['Bulan'] == 12).astype(int)
            
            # Create lag features with error handling
            try:
                for lag in range(1, 4):
                    df[f'lag_{lag}'] = df.groupby('Nama Item')['total_jumlah'].shift(lag)
            except Exception as e:
                st.error(f"Error saat membuat lag features: {str(e)}")
                logger.error(f"Lag features error: {str(e)}")
                return None
            
            # Create moving averages with error handling
            try:
                for window in [3, 6]:
                    df[f'ma_{window}'] = df.groupby('Nama Item')['total_jumlah'].rolling(
                        window=window, min_periods=1
                    ).mean().reset_index(level=0, drop=True)
            except Exception as e:
                st.error(f"Error saat membuat moving averages: {str(e)}")
                logger.error(f"Moving average error: {str(e)}")
                return None
            
            # Create difference features
            try:
                df['diff_1'] = df.groupby('Nama Item')['total_jumlah'].diff()
            except Exception as e:
                st.error(f"Error saat membuat difference features: {str(e)}")
                logger.error(f"Difference features error: {str(e)}")
                return None
            
            # Fill missing values
            df = df.fillna(0)
            
            logger.info("Feature preparation completed successfully")
            return df
            
    except Exception as e:
        st.error(f"Error tidak terduga saat memproses data: {str(e)}")
        logger.error(f"Unexpected error in prepare_features: {str(e)}")
        return None

@st.cache_data
def load_data() -> Optional[pd.DataFrame]:
    """
    Load data from CSV file with robust error handling.
    
    Returns:
        pd.DataFrame: Loaded and processed data or None if error
    """
    try:
        with st.spinner("Memuat data dari data.csv..."):
            df = pd.read_csv("data.csv")
            
            # Validate loaded data
            validation = validate_dataframe(df)
            if not validation['is_valid']:
                for error in validation['errors']:
                    st.error(error)
                logger.error(f"Data validation failed: {validation['errors']}")
                return None
            
            # Process features
            processed_df = prepare_features(df)
            if processed_df is not None:
                logger.info("Data loaded and processed successfully")
                return processed_df
            else:
                logger.error("Feature preparation failed")
                return None
                
    except FileNotFoundError:
        error_msg = "File 'data.csv' tidak ditemukan. Pastikan file data ada di direktori yang sama."
        st.error(error_msg)
        logger.error("Data file not found")
        return None
    except pd.errors.EmptyDataError:
        error_msg = "File 'data.csv' kosong atau tidak berisi data."
        st.error(error_msg)
        logger.error("Data file is empty")
        return None
    except pd.errors.ParserError as e:
        error_msg = f"Error parsing file 'data.csv': {str(e)}"
        st.error(error_msg)
        logger.error(f"CSV parsing error: {str(e)}")
        return None
    except Exception as e:
        error_msg = f"Error tidak terduga saat memuat data: {str(e)}"
        st.error(error_msg)
        logger.error(f"Unexpected error in load_data: {str(e)}")
        return None

def predict_future(df: pd.DataFrame, model, months: int = 3) -> Optional[pd.DataFrame]:
    """
    Predict future sales with robust error handling.
    
    Args:
        df: Input dataframe
        model: Trained model
        months: Number of months to predict
        
    Returns:
        pd.DataFrame: Future predictions or None if error
    """
    try:
        with st.spinner(f"Memperkirakan {months} bulan ke depan..."):
            if df is None or model is None:
                st.error("Data atau model tidak tersedia")
                return None
            
            # Validate input parameters
            if months <= 0 or months > 12:
                st.error("Jumlah bulan harus antara 1-12")
                return None
            
            last_data = df.groupby('Nama Item').tail(1).copy()
            
            # Calculate confidence interval
            try:
                clean_df = df.dropna()
                if not clean_df.empty:
                    feature_cols = ['Tahun', 'Bulan', 'quarter', 'is_start_year', 'is_end_year',
                                    'lag_1', 'lag_2', 'lag_3', 'ma_3', 'ma_6', 'diff_1']
                    X_current = clean_df[feature_cols]
                    y_current = clean_df['total_jumlah']
                    y_pred_current = model.predict(X_current)
                    residuals = y_current - y_pred_current
                    std_pred = residuals.std()
                else:
                    std_pred = 0
            except Exception as e:
                st.warning(f"Error menghitung confidence interval: {str(e)}")
                logger.warning(f"Confidence interval error: {str(e)}")
                std_pred = 0
            
            future_preds = []
            
            for i in range(1, months + 1):
                for _, row in last_data.iterrows():
                    try:
                        next_period = row['periode'] + pd.DateOffset(months=i)
                        
                        # Calculate lag features
                        if i == 1:
                            lag_1 = row['total_jumlah']
                            lag_2 = row['lag_1']
                            lag_3 = row['lag_2']
                        else:
                            prev_pred_df = pd.DataFrame(future_preds)
                            prev_pred_item = prev_pred_df[
                                (prev_pred_df['Nama Item'] == row['Nama Item']) & 
                                (prev_pred_df['periode'] == next_period - pd.DateOffset(months=1))
                            ]
                            
                            if not prev_pred_item.empty:
                                lag_1 = prev_pred_item['prediksi_jumlah'].iloc[0]
                                
                                if i >= 2:
                                    prev_2_pred_item = prev_pred_df[
                                        (prev_pred_df['Nama Item'] == row['Nama Item']) & 
                                        (prev_pred_df['periode'] == next_period - pd.DateOffset(months=2))
                                    ]
                                    lag_2 = prev_2_pred_item['prediksi_jumlah'].iloc[0] if not prev_2_pred_item.empty else row['lag_1']
                                else:
                                    lag_2 = row['lag_1']
                                
                                if i >= 3:
                                    prev_3_pred_item = prev_pred_df[
                                        (prev_pred_df['Nama Item'] == row['Nama Item']) & 
                                        (prev_pred_df['periode'] == next_period - pd.DateOffset(months=3))
                                    ]
                                    lag_3 = prev_3_pred_item['prediksi_jumlah'].iloc[0] if not prev_3_pred_item.empty else row['lag_2']
                                else:
                                    lag_3 = row['lag_2']
                            else:
                                lag_1 = row['total_jumlah']
                                lag_2 = row['lag_1']
                                lag_3 = row['lag_2']
                        
                        # Prepare features for prediction
                        features_input = {
                            'Tahun': next_period.year,
                            'Bulan': next_period.month,
                            'quarter': (next_period.month - 1) // 3 + 1,
                            'is_start_year': int(next_period.month == 1),
                            'is_end_year': int(next_period.month == 12),
                            'lag_1': lag_1,
                            'lag_2': lag_2,
                            'lag_3': lag_3,
                            'ma_3': (lag_1 + lag_2 + lag_3) / 3,
                            'ma_6': row['ma_6'] if 'ma_6' in row and not pd.isna(row['ma_6']) else 0,
                            'diff_1': lag_1 - lag_2
                        }
                        
                        # Make prediction
                        features_df = pd.DataFrame([features_input])
                        pred = model.predict(features_df)[0]
                        pred = max(pred, 0)  # Ensure non-negative
                        
                        # Calculate confidence interval
                        ci_lower = max(pred - 1.96 * std_pred, 0)
                        ci_upper = pred + 1.96 * std_pred
                        
                        future_preds.append({
                            'Nama Item': row['Nama Item'],
                            'periode': next_period,
                            'prediksi_jumlah': pred,
                            'CI_lower': ci_lower,
                            'CI_upper': ci_upper
                        })
                        
                    except Exception as e:
                        st.error(f"Error prediksi untuk {row['Nama Item']}: {str(e)}")
                        logger.error(f"Prediction error for {row['Nama Item']}: {str(e)}")
                        continue
            
            if future_preds:
                future_df = pd.DataFrame(future_preds)
                future_df['confidence_level'] = '95%'
                future_df = future_df.sort_values(by=['Nama Item', 'periode'])
                logger.info("Future predictions completed successfully")
                return future_df
            else:
                st.error("Tidak ada prediksi yang berhasil dibuat")
                logger.error("No predictions were created")
                return None
                
    except Exception as e:
        st.error(f"Error tidak terduga saat prediksi: {str(e)}")
        logger.error(f"Unexpected error in predict_future: {str(e)}")
        return None 