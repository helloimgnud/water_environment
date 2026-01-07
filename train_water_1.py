import itertools
from prophet import Prophet
from prophet.diagnostics import cross_validation, performance_metrics
from prophet.serialize import model_to_json
import pandas as pd
import numpy as np
import time
import os
import json
from datetime import datetime
from sklearn.metrics import mean_absolute_error, mean_squared_error

# ===============================
# CẤU HÌNH CHUNG - BẠN CHỈ CẦN SỬA DÒNG NÀY
# ===============================
TARGET_COLUMN = 'nhiet_do_nuoc'  # ← Thay thành 'do_man' hoặc 'nhiet_do_nuoc'
TARGET_NAME = 'DO (mặn)' if TARGET_COLUMN == 'do_man' else 'Nhiệt độ nước'

INPUT_ROOT = r"D:\quan_ly_tai_nguyen_bien\dataset\data_outliers_as_nan\04_WATER_QUALITY_SAMPLES_MIDDLE_WATER"
OUTPUT_ROOT = r"D:\quan_ly_tai_nguyen_bien\dataset\data_outliers_as_nan\prophet_models_water_middle"

# Cấu hình giống hệt mã gốc
FOURIER_ORDER = 30
USE_LOG_TRANSFORM = True
INTERVAL_WIDTH = 0.95

# Fixed params giống mã gốc
fixed_params = {
    'yearly_seasonality': True,
    'weekly_seasonality': False,
    'daily_seasonality': False,
    'interval_width': INTERVAL_WIDTH
}

# Grid search giống hệt mã gốc
param_grid = {
    'growth': ['linear'],
    'n_changepoints': [10, 25, 50],
    'changepoint_range': [0.8, 0.9, 0.95],
    'seasonality_mode': ['additive', 'multiplicative'],
    'seasonality_prior_scale': [1.0, 5.0, 10.0, 20.0],
    'changepoint_prior_scale': [0.01, 0.05, 0.1]
}

grid = list(itertools.product(*param_grid.values()))
os.makedirs(OUTPUT_ROOT, exist_ok=True)

def calculate_cv_params(df):
    total_days = (df['ds'].max() - df['ds'].min()).days
    total_months = total_days / 30.44
    initial = int(max(1, total_months * 0.7) * 30.44)
    period  = int(max(1, total_months * 0.05) * 30.44)
    horizon = int(max(1, total_months * 0.1) * 30.44)
    return f"{initial} days", f"{period} days", f"{horizon} days"

# ===============================
# BẮT ĐẦU TRAIN TỰ ĐỘNG
# ===============================
total_start_time = time.time()
processed_count = 0

print(f"🚀 BẮT ĐẦU TRAIN TỰ ĐỘNG - NƯỚC MẶT (SURFACE WATER)")
print(f"Chỉ tiêu được chọn: {TARGET_COLUMN.upper()} ({TARGET_NAME})")
print(f"Input: {INPUT_ROOT}")
print(f"Output: {OUTPUT_ROOT}")
print(f"Số tổ hợp grid search: {len(grid)}")
print("="*100)

for area_folder in os.listdir(INPUT_ROOT):
    area_path = os.path.join(INPUT_ROOT, area_folder)
    if not os.path.isdir(area_path):
        continue
    
    print(f"\n📂 Khu vực: {area_folder}")
    
    for file_name in os.listdir(area_path):
        if not file_name.endswith('.csv'):
            continue
            
        file_path = os.path.join(area_path, file_name)
        station_name = os.path.splitext(file_name)[0]
        
        print(f"   📄 Trạm: {station_name} ({file_name})")
        
        try:
            df_raw = pd.read_csv(file_path)
            df_raw['thoi_gian'] = pd.to_datetime(df_raw['thoi_gian'])
        except Exception as e:
            print(f"      ❌ Lỗi đọc file: {e}")
            continue
        
        if TARGET_COLUMN not in df_raw.columns:
            print(f"      ⚠️  Không có cột {TARGET_COLUMN} → Bỏ qua")
            continue
        
        # === CƠ CHẾ KIỂM TRA ĐÃ TRAIN CHƯA ===
        target_dir = os.path.join(OUTPUT_ROOT, area_folder, station_name, TARGET_COLUMN)
        model_path = os.path.join(target_dir, "prophet_model.json")
        config_path = os.path.join(target_dir, "config.json")
        
        if os.path.exists(model_path) and os.path.exists(config_path):
            print(f"      📦 Đã train trước đó (model + config tồn tại) → Bỏ qua trạm này")
            continue
        
        print(f"      🔬 Đang train: {TARGET_COLUMN.upper()} ({TARGET_NAME})")
        print(f"         🚀 Bắt đầu grid search ({len(grid)} tổ hợp)...")
        
        try:
            # Chuẩn bị dữ liệu giống mã gốc
            df_prophet = (
                df_raw[['thoi_gian', TARGET_COLUMN]]
                .rename(columns={'thoi_gian': 'ds', TARGET_COLUMN: 'y'})
                .dropna()
                .sort_values('ds')
                .reset_index(drop=True)
            )
            
            if len(df_prophet) < 20:
                print(f"         ❌ Dữ liệu quá ít ({len(df_prophet)} điểm) → Bỏ qua")
                continue
            
            y_original = df_prophet['y'].copy()
            
            if USE_LOG_TRANSFORM:
                df_prophet['y'] = np.log1p(df_prophet['y'])
            
            initial_cv, period_cv, horizon_cv = calculate_cv_params(df_prophet)
            
            # Grid search với progress realtime giống mã gốc
            best_mae = float('inf')
            best_params = None
            best_cv_metrics = None
            
            for idx, params in enumerate(grid, 1):
                g, n_cp, cp_range, s_mode, s_prior, cp_prior = params
                progress = f"         [{idx:3d}/{len(grid)} | {idx/len(grid)*100:5.1f}%] "
                
                try:
                    model = Prophet(**fixed_params,
                                    growth=g,
                                    n_changepoints=n_cp,
                                    changepoint_range=cp_range,
                                    seasonality_mode=s_mode,
                                    seasonality_prior_scale=s_prior,
                                    changepoint_prior_scale=cp_prior)
                    model.add_seasonality(name='yearly', period=365.25, fourier_order=FOURIER_ORDER)
                    model.fit(df_prophet)
                    
                    df_cv = cross_validation(model, initial=initial_cv, period=period_cv,
                                            horizon=horizon_cv, parallel="threads")
                    df_p = performance_metrics(df_cv)
                    mae = df_p['mae'].mean()
                    mape = df_p['mape'].mean()
                    rmse = df_p['rmse'].mean()
                    
                    if mae < best_mae:
                        best_mae = mae
                        best_params = params
                        best_cv_metrics = {'mape': mape, 'mae': mae, 'rmse': rmse}
                        print(f"{progress}🎯 NEW BEST | n_cp={n_cp}, cp_range={cp_range:.2f}, "
                              f"mode={s_mode}, s_prior={s_prior}, cp_prior={cp_prior} → "
                              f"MAPE={mape:.3f}% MAE={mae:.3f} RMSE={rmse:.3f} 💎")
                    else:
                        print(f"{progress}n_cp={n_cp}, cp_range={cp_range:.2f}, mode={s_mode}, "
                              f"s_prior={s_prior}, cp_prior={cp_prior} → "
                              f"MAPE={mape:.3f}% MAE={mae:.3f} (best: {best_mae:.3f})")
                
                except Exception as e:
                    print(f"{progress}❌ LỖI: {str(e)[:80]}...")
                    continue
            
            if best_params is None:
                print(f"         ❌ Grid search thất bại hoàn toàn → Bỏ qua trạm này")
                continue
            
            # Train final model giống mã gốc
            g, n_cp, cp_range, s_mode, s_prior, cp_prior = best_params
            final_model = Prophet(**fixed_params,
                                  growth=g,
                                  n_changepoints=n_cp,
                                  changepoint_range=cp_range,
                                  seasonality_mode=s_mode,
                                  seasonality_prior_scale=s_prior,
                                  changepoint_prior_scale=cp_prior)
            final_model.add_seasonality(name='yearly', period=365.25, fourier_order=FOURIER_ORDER)
            final_model.fit(df_prophet)
            
            # Dự báo giống mã gốc (periods=12, freq='M')
            future = final_model.make_future_dataframe(periods=12, freq='M')
            forecast = final_model.predict(future)
            
            # Inverse transform giống mã gốc
            if USE_LOG_TRANSFORM:
                forecast[['yhat', 'yhat_lower', 'yhat_upper']] = np.expm1(
                    forecast[['yhat', 'yhat_lower', 'yhat_upper']]
                )
            
            # Cắt forecast_hist giống hệt mã gốc để tính final metrics
            forecast_hist = forecast.iloc[:len(y_original)]
            
            mae_final = mean_absolute_error(y_original, forecast_hist['yhat'])
            rmse_final = np.sqrt(mean_squared_error(y_original, forecast_hist['yhat']))
            mape_final = np.mean(np.abs((y_original - forecast_hist['yhat']) / y_original)) * 100
            
            # Lưu model + config
            os.makedirs(target_dir, exist_ok=True)
            
            with open(model_path, 'w', encoding='utf-8') as f:
                f.write(model_to_json(final_model))
            
            config = {
                'area': area_folder,
                'station': station_name,
                'target_column': TARGET_COLUMN,
                'target_name': TARGET_NAME,
                'train_start_date': str(df_prophet['ds'].min().date()),
                'train_end_date': str(df_prophet['ds'].max().date()),
                'n_observations': len(df_prophet),
                'use_log_transform': USE_LOG_TRANSFORM,
                'fourier_order': FOURIER_ORDER,
                'best_cv_mae_logspace': float(best_mae),
                'best_cv_mape_logspace': float(best_cv_metrics['mape']),
                'best_cv_rmse_logspace': float(best_cv_metrics['rmse']),
                'final_in_sample_mae': float(mae_final),
                'final_in_sample_rmse': float(rmse_final),
                'final_in_sample_mape': float(mape_final),
                'best_params': {
                    'n_changepoints': n_cp,
                    'changepoint_range': cp_range,
                    'seasonality_mode': s_mode,
                    'seasonality_prior_scale': s_prior,
                    'changepoint_prior_scale': cp_prior
                },
                'trained_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, default=str)
            
            print(f"         ✅ ĐÃ LƯU MODEL: {area_folder}/{station_name}/{TARGET_COLUMN}/")
            print(f"            → Final MAE: {mae_final:.3f} | RMSE: {rmse_final:.3f} | MAPE: {mape_final:.2f}%")
            processed_count += 1
            
        except Exception as e:
            print(f"         ❌ Lỗi nghiêm trọng khi train: {str(e)}")
            continue

print("="*100)
total_time = time.time() - total_start_time
print(f"🎉 HOÀN TẤT! Đã train và lưu thành công {processed_count} model mới cho chỉ tiêu: {TARGET_COLUMN.upper()}")
print(f"⏱️ Tổng thời gian: {total_time/60:.1f} phút")
print(f"📁 Output: {OUTPUT_ROOT}")
print("   Cấu trúc: <area>/<station>/<target>/prophet_model.json + config.json")
print("   → Chỉ train những trạm chưa có model đầy đủ (model.json + config.json)")
print("="*100)