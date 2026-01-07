import itertools
from prophet import Prophet
from prophet.diagnostics import cross_validation, performance_metrics
import pandas as pd
import numpy as np
import time
import matplotlib.pyplot as plt
from sklearn.metrics import mean_absolute_error, mean_squared_error

start = time.time()

# ===============================
# CẤU HÌNH CHỈ TIÊU DỰ BÁO
# ===============================
target_column = 'cd'
target_name   = 'cd'
fourier = 5
use_log_transform = False

# ===============================
# BƯỚC 1: CHUẨN BỊ DỮ LIỆU
# ===============================
file_path = r"D:\quan_ly_tai_nguyen_bien\dataset\data_outliers_as_nan\01_SEDIMENT_SAMPLES\Mirs Bay\MS8.csv"
df = pd.read_csv(file_path)
df['thoi_gian'] = pd.to_datetime(df['thoi_gian'])

df_prophet = (
    df[['thoi_gian', target_column]]
    .rename(columns={'thoi_gian': 'ds', target_column: 'y'})
    .dropna()
    .sort_values('ds')
    .reset_index(drop=True)
)

# Lưu dữ liệu gốc để đánh giá sau
y_original = df_prophet['y'].copy()

# Log transform (nếu bật)
if use_log_transform:
    df_prophet['y'] = np.log1p(df_prophet['y'])
    print(f"✔ Đã áp dụng log(1 + y) cho {target_column}")

# ===============================
# BƯỚC 2: CV PARAMETERS
# ===============================
def calculate_cv_params(df, initial_pct=0.7, period_pct=0.05, horizon_pct=0.1):
    total_days = (df['ds'].max() - df['ds'].min()).days
    total_months = total_days / 30.44

    initial = int(max(1, total_months * initial_pct) * 30.44)
    period  = int(max(1, total_months * period_pct) * 30.44)
    horizon = int(max(1, total_months * horizon_pct) * 30.44)

    return f"{initial} days", f"{period} days", f"{horizon} days"

initial_cv, period_cv, horizon_cv = calculate_cv_params(df_prophet)
print(f"🔧 CV Params: initial={initial_cv}, period={period_cv}, horizon={horizon_cv}")

# ===============================
# CẤU HÌNH CỐ ĐỊNH
# ===============================
fixed_params = {
    'yearly_seasonality': False,
    'weekly_seasonality': False,
    'daily_seasonality': False,
    'interval_width': 0.8
}

param_grid = {
    'growth': ['linear'],
    'n_changepoints': [5, 10, 15, 25],
    'changepoint_range': [0.8, 0.9],
    'seasonality_mode': ['additive'],
    'seasonality_prior_scale': [0.5, 1.0, 3.0, 5.0, 7.0, 10.0],
    'changepoint_prior_scale': [0.01, 0.05, 0.1]
}

# Tạo grid
grid = list(itertools.product(
    param_grid['growth'],
    param_grid['n_changepoints'],
    param_grid['changepoint_range'],
    param_grid['seasonality_mode'],
    param_grid['seasonality_prior_scale'],
    param_grid['changepoint_prior_scale']
))

best_mae = float('inf')
best_params = None
best_metrics = None
results = []

print(f"\n🚀 Tổng số tổ hợp cần thử: {len(grid):,} (khoảng {len(grid)*0.3:.0f}-{len(grid)*0.8:.0f}s)")
print("Bắt đầu grid search với tracking realtime...\n")

# ===============================
# GRID SEARCH (giữ linear growth - không floor)
# ===============================
for idx, params in enumerate(grid, 1):
    g, n_cp, cp_range, s_mode, s_prior, cp_prior = params
    
    progress = f"[{idx:3d}/{len(grid)} | {idx/len(grid)*100:5.1f}%] "
    
    try:
        model = Prophet(
            **fixed_params,
            growth=g,
            n_changepoints=n_cp,
            changepoint_range=cp_range,
            seasonality_mode=s_mode,
            seasonality_prior_scale=s_prior,
            changepoint_prior_scale=cp_prior
        )
        
        model.add_seasonality(name='yearly', period=365.25, fourier_order=fourier)
        model.fit(df_prophet)

        df_cv = cross_validation(
            model,
            initial=initial_cv,
            period=period_cv,
            horizon=horizon_cv,
            parallel="threads"
        )

        df_p = performance_metrics(df_cv)
        mape = df_p['mape'].mean()
        mae  = df_p['mae'].mean()
        rmse = df_p['rmse'].mean()
        
        metrics = {'mape': mape, 'mae': mae, 'rmse': rmse}
        results.append({'params': params, **metrics})

        if mae < best_mae:
            best_mae = mae
            best_params = params
            best_metrics = metrics
            print(f"{progress}🎯 NEW BEST | "
                  f"n_cp={n_cp}, cp_range={cp_range:.2f}, mode={s_mode}, "
                  f"s_prior={s_prior}, cp_prior={cp_prior} → "
                  f"MAPE={mape:.3f}% MAE={mae:.3f} RMSE={rmse:.3f} 💎")
        else:
            print(f"{progress}n_cp={n_cp}, cp_range={cp_range:.2f}, mode={s_mode}, "
                  f"s_prior={s_prior}, cp_prior={cp_prior} → "
                  f"MAPE={mape:.3f}% MAE={mae:.3f} RMSE={rmse:.3f} (best MAE: {best_mae:.3f})")

    except Exception as e:
        print(f"{progress}❌ LỖI: {str(e)[:80]}...")

# ===============================
# IN KẾT QUẢ BEST MODEL TỪ GRID SEARCH
# ===============================
print("\n" + "="*80)
print("🏆 BỘ THAM SỐ TỐT NHẤT (CV trên LOG-SPACE)")
print("="*80)

g, n_cp, cp_range, s_mode, s_prior, cp_prior = best_params
print(f"1. n_cp={n_cp}, cp_range={cp_range:.2f}, mode={s_mode}, "
      f"s_prior={s_prior}, cp_prior={cp_prior} → "
      f"MAPE={best_metrics['mape']:.3f}% MAE={best_metrics['mae']:.3f} RMSE={best_metrics['rmse']:.3f} 🎯")

print("\n" + "="*80)
print("⭐ BEST MODEL CHI TIẾT")
print("="*80)
print(f"Growth (grid): {g}")
print(f"n_changepoints: {n_cp}")
print(f"changepoint_range: {cp_range}")
print(f"seasonality_mode: {s_mode}")
print(f"seasonality_prior_scale: {s_prior}")
print(f"changepoint_prior_scale: {cp_prior}")
print(f"CV MAPE: {best_metrics['mape']:.4f}%")
print(f"CV MAE: {best_mae:.4f}")
print(f"CV RMSE: {best_metrics['rmse']:.4f}")

# ===============================
# TRAIN FINAL MODEL VỚI LOGISTIC GROWTH + CAP & FLOOR
# ===============================
print("\n🔄 Training final model với logistic growth + cap (q0.98 * 1.2) & floor=0...")

# Tính cap dựa trên quantile 0.98 * 1.2
q98 = y_original.quantile(0.98)
cap_value = q98 * 1.2
floor_value = 0.0

print(f"🔹 Quantile 0.98: {q98:.3f} mg/L → Cap = {cap_value:.3f} mg/L (q98 * 1.2)")

# Thiết lập cho dữ liệu huấn luyện
df_prophet['cap'] = cap_value
df_prophet['floor'] = floor_value

# Tạo model logistic
best_model = Prophet(
    **fixed_params,
    growth='logistic',
    n_changepoints=n_cp,
    changepoint_range=cp_range,
    seasonality_mode=s_mode,
    seasonality_prior_scale=s_prior,
    changepoint_prior_scale=cp_prior
)

best_model.add_seasonality(name='yearly', period=365.25, fourier_order=fourier)
best_model.fit(df_prophet)

# Tạo future và thêm cap/floor giống hệt
future = best_model.make_future_dataframe(periods=12, freq='M')
future['cap'] = cap_value
future['floor'] = floor_value

forecast = best_model.predict(future)

# ===============================
# KIỂM TRA VÀ ĐÁNH GIÁ
# ===============================
print("\n📈 Chi tiết dự báo 12 tháng tương lai:")
print(forecast.tail(12)[['ds', 'yhat', 'yhat_lower', 'yhat_upper']])

forecast['interval_width'] = forecast['yhat_upper'] - forecast['yhat_lower']
print("\nBiên độ khoảng tin cậy ở future:")
print(forecast.tail(12)['interval_width'])

if use_log_transform:
    forecast[['yhat', 'yhat_lower', 'yhat_upper']] = np.expm1(
        forecast[['yhat', 'yhat_lower', 'yhat_upper']]
    )

forecast_hist = forecast.iloc[:len(y_original)]
mae_final = mean_absolute_error(y_original, forecast_hist['yhat'])
rmse_final = np.sqrt(mean_squared_error(y_original, forecast_hist['yhat']))
mape_final = np.mean(np.abs((y_original - forecast_hist['yhat']) / y_original)) * 100

print("\n" + "="*80)
print("✅ ĐÁNH GIÁ CUỐI CÙNG (SCALE GỐC – mg/L) - FINAL FIT")
print("="*80)
print(f"MAE  : {mae_final:.3f} mg/L")
print(f"RMSE : {rmse_final:.3f} mg/L")
print(f"MAPE : {mape_final:.2f} %")

# ===============================
# TRỰC QUAN HÓA
# ===============================
plt.figure(figsize=(15,8))
plt.plot(df_prophet['ds'], y_original, 'o-', markersize=4, label='Thực tế (As - mg/L)', alpha=0.7)
plt.plot(forecast['ds'], forecast['yhat'], 'r-', linewidth=2.5, label='Dự báo (Logistic + Floor=0)')
plt.fill_between(
    forecast['ds'],
    forecast['yhat_lower'],
    forecast['yhat_upper'],
    alpha=0.25,
    color='red',
    label='Khoảng tin cậy 80%'
)
plt.axvline(df_prophet['ds'].max(), color='gray', linestyle='--', linewidth=2, label='Bắt đầu dự báo')
plt.xlabel("Thời gian", fontsize=12)
plt.ylabel(f"{target_name} (mg/L)", fontsize=12)
plt.title(f"🚀 Dự báo {target_name.upper()} - Deep Bay DS1 (Logistic Growth + Floor=0)\n"
          f"Best: MAPE={mape_final:.1f}% | RMSE={rmse_final:.2f} mg/L", fontsize=14, fontweight='bold')
plt.legend(fontsize=11)
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()

print("\n📊 Components plot:")
best_model.plot_components(forecast)
plt.suptitle(f"Phân tích thành phần - {target_name.upper()} (Best Model - Logistic + Floor=0)", fontsize=16, fontweight='bold')
plt.tight_layout()
plt.show()

total_time = time.time() - start
print(f"\n⏱️ Tổng thời gian chạy: {total_time:.1f}s ({total_time/len(grid):.1f}s/tổ_hợp)")
print(f"✅ Hoàn thành! Dự báo giờ không có giá trị âm và ổn định hơn nhờ logistic growth + floor=0.")

# Lưu kết quả grid search
results_df = pd.DataFrame(results)
results_df.to_csv(f'prophet_gridsearch_results_{target_column}.csv', index=False)
print(f"💾 Đã lưu {len(results)} kết quả grid search → prophet_gridsearch_results_{target_column}.csv")

# ===============================
# LƯU MODEL ĐỂ SỬ DỤNG SAU (THÊM PHẦN NÀY VÀO CUỐI SCRIPT)
# ===============================
from prophet.serialize import model_to_json
import joblib
import json
import os

# Tạo thư mục lưu nếu chưa có (tùy chọn)
save_dir = "prophet_saved_models"
os.makedirs(save_dir, exist_ok=True)

# Tên file chung
model_name = f"prophet_model_{target_column}_deepbay_ds1"

# 1. Lưu model bằng JSON (phương thức chính thức của Prophet)
json_path = os.path.join(save_dir, f"{model_name}.json")
with open(json_path, 'w', encoding='utf-8') as fout:
    fout.write(model_to_json(best_model))
print(f"✅ Đã lưu model (JSON): {json_path}")

# 2. Lưu model bằng joblib/pickle (nhanh, tiện dùng sau này)
pkl_path = os.path.join(save_dir, f"{model_name}.pkl")
joblib.dump(best_model, pkl_path)
print(f"✅ Đã lưu model (Pickle): {pkl_path}")

# 3. Lưu cấu hình quan trọng (cap, floor, thông tin dữ liệu)
config = {
    'target_column': target_column,
    'target_name': target_name,
    'site': 'Deep Bay DS1',
    'train_start_date': str(df_prophet['ds'].min().date()),
    'train_end_date': str(df_prophet['ds'].max().date()),
    'total_observations': len(df_prophet),
    'cap_value': float(cap_value),
    'floor_value': float(floor_value),
    'q98_original': float(q98),
    'fourier_order': fourier,
    'use_log_transform': use_log_transform,
    'final_mae': float(mae_final),
    'final_rmse': float(rmse_final),
    'final_mape': float(mape_final),
    'best_params': {
        'n_changepoints': n_cp,
        'changepoint_range': cp_range,
        'seasonality_mode': s_mode,
        'seasonality_prior_scale': s_prior,
        'changepoint_prior_scale': cp_prior
    }
}

config_path = os.path.join(save_dir, f"{model_name}_config.json")
with open(config_path, 'w', encoding='utf-8') as f:
    json.dump(config, f, indent=4, default=str)

print(f"✅ Đã lưu cấu hình model: {config_path}")

print("\n" + "="*80)
print("🎉 HOÀN TẤT LƯU MODEL!")
print("="*80)
print(f"Tất cả file đã được lưu trong thư mục: ./{save_dir}/")
print("   • Model JSON:      dễ đọc, chính thức")
print("   • Model Pickle:    nhanh khi load")
print("   • Config JSON:     chứa cap, floor, thông tin train")
print("\nSau này bạn chỉ cần load model + config → predict ngay lập tức!")
print("Ví dụ load & predict sẽ được cung cấp riêng nếu cần.")
print("="*80)