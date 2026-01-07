import os
import pandas as pd
import numpy as np

input_base_dir = r"D:\quan_ly_tai_nguyen_bien\dataset\data_split_vertical"
output_base_dir = r"D:\quan_ly_tai_nguyen_bien\dataset\data_outliers_as_nan_2"

os.makedirs(output_base_dir, exist_ok=True)

folders = {
    "01_SEDIMENT_SAMPLES": {
        "cols": ['as', 'cd', 'pb', 'cu', 'zn'],
        "method": "median_k_trimmed_std",
        "k": 5.0,
        "trim_ratio": 0.05
    },
    "03_WATER_QUALITY_SAMPLES_SURFACE_WATER": {
        "cols": ['do_man', 'ph', 'nh3', 'nhiet_do_nuoc', 'bod5', 'tss'],
        "method": "iqr",             # ← THAY BẰNG IQR
        "multiplier": 1.5            # ← Hệ số: 1.5 (mặc định), 2.0 (vừa), 2.5–3.0 (nghiêm ngặt)
    },
    "04_WATER_QUALITY_SAMPLES_MIDDLE_WATER": {
        "cols": ['do_man', 'ph', 'nhiet_do_nuoc', 'bod5', 'tss'],
        "method": "iqr",
        "multiplier": 1.5
    },
    "05_WATER_QUALITY_SAMPLES_BOTTOM_WATER": {
        "cols": ['do_man', 'ph', 'nhiet_do_nuoc', 'bod5', 'tss'],
        "method": "iqr",
        "multiplier": 1.5
    }
}

print("PHÁT HIỆN OUTLIERS VÀ ĐẶT THÀNH NaN – PHIÊN BẢN IQR CHO CHẤT LƯỢNG NƯỚC")
print("=" * 80)

processed_files = 0
total_outliers_marked = 0

for folder_name, config in folders.items():
    input_folder_path = os.path.join(input_base_dir, folder_name)
    output_folder_path = os.path.join(output_base_dir, folder_name)
    os.makedirs(output_folder_path, exist_ok=True)
    
    print(f"\nXử lý folder: {folder_name}")
    
    for root, dirs, files in os.walk(input_folder_path):
        rel_root = os.path.relpath(root, input_folder_path)
        current_output_root = os.path.join(output_folder_path, rel_root)
        os.makedirs(current_output_root, exist_ok=True)
        
        for filename in files:
            if not filename.lower().endswith(".csv"):
                continue
            
            input_filepath = os.path.join(root, filename)
            output_filepath = os.path.join(current_output_root, filename)
            
            print(f"   → File: {os.path.relpath(input_filepath, input_base_dir)}")
            
            try:
                df = pd.read_csv(input_filepath)
                
                if 'thoi_gian' in df.columns:
                    df['thoi_gian'] = pd.to_datetime(df['thoi_gian'], errors='coerce')
                df = df.sort_values('thoi_gian') if 'thoi_gian' in df.columns else df.reset_index(drop=True)
                
                numeric_cols = config['cols']
                method = config['method']
                
                for col in numeric_cols:
                    if col not in df.columns:
                        continue
                    
                    outlier_mask = pd.Series([False] * len(df), index=df.index)
                    
                    data = df[col].dropna()
                    if len(data) < 10:
                        print(f"      - Cột {col}: Quá ít dữ liệu ({len(data)} mẫu) → bỏ qua")
                        continue

                    if method == "median_k_trimmed_std":
                        # Giữ nguyên cho trầm tích (như cũ)
                        k = config.get('k', 2.0)
                        trim_ratio = config.get('trim_ratio', 0.05)
                        
                        median_val = data.median()
                        distances = np.abs(data - median_val)
                        trim_threshold = distances.quantile(1 - trim_ratio)
                        trimmed_mask = distances <= trim_threshold
                        trimmed_data = data[trimmed_mask]
                        
                        if len(trimmed_data) == 0 or trimmed_data.std() == 0:
                            print(f"      - Cột {col}: Sau trim, Std = 0 → bỏ qua")
                            continue
                        
                        std_trimmed = trimmed_data.std()
                        upper_bound = median_val + k * std_trimmed
                        lower_bound = median_val - k * std_trimmed
                        
                        outlier_mask = (df[col] > upper_bound) | (df[col] < lower_bound)
                        
                        num_outliers = outlier_mask.sum()
                        if num_outliers > 0:
                            print(f"      - Cột {col}: {num_outliers} outliers (Median + {k}×TrimmedStd) → đặt thành NaN")

                    elif method == "iqr":
                        multiplier = config.get('multiplier', 1.5)  # 1.5 mặc định, khuyến nghị 2.0 cho nước
                        
                        Q1 = df[col].quantile(0.25)
                        Q3 = df[col].quantile(0.75)
                        IQR_val = Q3 - Q1
                        
                        if IQR_val == 0:
                            print(f"      - Cột {col}: IQR = 0 → bỏ qua phát hiện outlier")
                            continue
                        
                        lower_bound = Q1 - multiplier * IQR_val
                        upper_bound = Q3 + multiplier * IQR_val
                        
                        outlier_mask = (df[col] < lower_bound) | (df[col] > upper_bound)
                        
                        num_outliers = outlier_mask.sum()
                        if num_outliers > 0:
                            print(f"      - Cột {col}: {num_outliers} outliers (IQR × {multiplier}) → đặt thành NaN")

                    # Áp dụng và đếm
                    if outlier_mask.sum() > 0:
                        df.loc[outlier_mask, col] = np.nan
                        total_outliers_marked += outlier_mask.sum()

                df.to_csv(output_filepath, index=False, encoding="utf-8-sig")
                processed_files += 1
                
            except Exception as e:
                print(f"   → LỖI: {e}")

print("=" * 80)
print(f"HOÀN TẤT! Đã xử lý {processed_files} file")
print(f"Tổng outliers được đặt thành NaN: {total_outliers_marked}")
print(f"Kết quả lưu vào folder mới: {output_base_dir}")
print("\nLưu ý: IQR không xét thời gian → có thể loại nhầm xu hướng mùa vụ.")
print("Khuyến nghị: Dùng multiplier = 2.0 hoặc 2.5 để tránh over-detect.")

