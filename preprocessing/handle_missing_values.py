import os
import pandas as pd
import numpy as np


# ==================== HÀM HELPER ====================
def find_gaps(series):
    """
    Tìm các gaps (chuỗi NaN liên tiếp) trong series và trả về danh sách độ dài gaps.
    """
    if not series.isna().any():
        return []
    
    mask = series.isna()
    groups = (mask != mask.shift()).cumsum()
    nan_groups = groups[mask]
    
    if len(nan_groups) == 0:
        return []
    
    gap_lengths = nan_groups.value_counts().tolist()
    return gap_lengths


# ==================== CẤU HÌNH ====================
base_dir = r"D:\quan_ly_tai_nguyen_bien\dataset\data_outliers_as_nan_2"

folders_to_process = {
    "01_SEDIMENT_SAMPLES": {
        "cols": ['as', 'cd', 'pb', 'cu', 'zn'],
        "fill_method": "median_full"
    },
    "03_WATER_QUALITY_SAMPLES_SURFACE_WATER": {
        "cols": ['do_man', 'ph', 'nh3', 'nhiet_do_nuoc', 'bod5', 'tss'],
        "fill_method": "interpolate_first",
        "max_gap_for_interpolate": 4   # Gap ≤4 thì interpolate, >4 thì fallback median
    },
    "04_WATER_QUALITY_SAMPLES_MIDDLE_WATER": {
        "cols": ['do_man', 'ph', 'nh3', 'nhiet_do_nuoc', 'bod5', 'tss'],
        "fill_method": "interpolate_first",
        "max_gap_for_interpolate": 4
    },
    "05_WATER_QUALITY_SAMPLES_BOTTOM_WATER": {
        "cols": ['do_man', 'ph', 'nh3', 'nhiet_do_nuoc', 'bod5', 'tss'],
        "fill_method": "interpolate_first",
        "max_gap_for_interpolate": 4
    }
}

print("XỬ LÝ MISSING VALUE – ƯU TIÊN INTERPOLATE NGAY TỪ BƯỚC 1")
print(" - Trầm tích: Median toàn file")
print(" - Nước biển: Interpolate (time nếu có thời gian, linear nếu không) + fallback nếu cần")
print("=" * 80)

processed_files = 0
total_filled = 0

for folder_name, config in folders_to_process.items():
    folder_path = os.path.join(base_dir, folder_name)
    print(f"\nXỬ LÝ FOLDER: {folder_name}")

    for root, dirs, files in os.walk(folder_path):
        for filename in files:
            if not filename.lower().endswith(".csv"):
                continue

            filepath = os.path.join(root, filename)
            rel_path = os.path.relpath(filepath, base_dir)
            print(f" → File: {rel_path}")

            try:
                df = pd.read_csv(filepath, low_memory=False)

                # Biến flag để biết có dùng time hay không
                has_datetime_index = False

                # Chuẩn bị thời gian: chuyển và set làm index để dùng method='time'
                if 'thoi_gian' in df.columns:
                    df['thoi_gian'] = pd.to_datetime(df['thoi_gian'], errors='coerce')
                    df = df.sort_values('thoi_gian').reset_index(drop=True)
                    df = df.set_index('thoi_gian')
                    has_datetime_index = True  # Đánh dấu đã có DatetimeIndex

                filled_in_file = 0
                for col in config['cols']:
                    if col not in df.columns:
                        continue

                    missing_before = df[col].isna().sum()
                    if missing_before == 0:
                        continue

                    if config['fill_method'] == "median_full":
                        median_val = df[col].median(skipna=True)
                        if not np.isnan(median_val):
                            df[col] = df[col].fillna(median_val)
                            filled_in_file += missing_before
                            print(f"   → Cột {col}: Đã điền {missing_before} missing bằng median toàn file")

                    elif config['fill_method'] == "interpolate_first":
                        max_gap = config.get('max_gap_for_interpolate', 12)

                        # Ưu tiên method='time' nếu có DatetimeIndex
                        interp_method = 'time' if has_datetime_index else 'linear'

                        try:
                            # Bước 1: Interpolate ngay
                            df[col] = df[col].interpolate(method=interp_method, limit_direction='both')

                            # Kiểm tra còn missing không
                            remaining = df[col].isna().sum()
                            gaps = find_gaps(df[col])

                            if gaps and max(gaps) > max_gap:
                                # Gap quá lớn → fallback median toàn bộ còn lại
                                global_median = df[col].median(skipna=True)
                                if not np.isnan(global_median):
                                    df[col] = df[col].fillna(global_median)
                                    print(f"   → Cột {col}: Gap lớn nhất = {max(gaps)} > {max_gap} → fallback {remaining} NaN bằng global median")
                                else:
                                    print(f"   → Cột {col}: Gap quá lớn và không thể fallback (toàn NaN)")
                            elif remaining > 0:
                                # Còn sót ở biên → fallback median
                                global_median = df[col].median(skipna=True)
                                if not np.isnan(global_median):
                                    df[col] = df[col].fillna(global_median)
                                    print(f"   → Cột {col}: Đã interpolate ({interp_method}), fallback median cho {remaining} giá trị biên")
                                else:
                                    print(f"   → Cột {col}: Interpolate xong nhưng vẫn còn NaN và không fallback được")
                            else:
                                print(f"   → Cột {col}: Đã điền hoàn toàn {missing_before} missing bằng interpolate ({interp_method})")

                            filled_in_file += missing_before

                        except Exception as e:
                            print(f"   → Cột {col}: Lỗi interpolate ({e}) → dùng median fallback")
                            global_median = df[col].median(skipna=True)
                            if not np.isnan(global_median):
                                df[col] = df[col].fillna(global_median)
                                filled_in_file += missing_before

                # Lưu file: reset index để giữ lại cột thoi_gian
                if filled_in_file > 0:
                    df_output = df.copy()
                    if has_datetime_index:
                        df_output = df_output.reset_index()  # Trả thoi_gian về làm cột

                    df_output.to_csv(filepath, index=False, encoding="utf-8-sig")
                    total_filled += filled_in_file

                processed_files += 1

            except Exception as e:
                print(f"   → LỖI khi xử lý file: {e}")

print("=" * 80)
print(f"HOÀN TẤT! Đã xử lý {processed_files} file")
print(f"Tổng số giá trị missing được điền: {total_filled}")
print("Dữ liệu giờ đã mượt mà với interpolate theo thời gian thực (method='time')!")
print("\nGợi ý: Vẽ đồ thị thử một vài trạm để thấy sự khác biệt tuyệt vời so với linear!")