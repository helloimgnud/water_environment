import os
import pandas as pd

# ==================== CẤU HÌNH ====================
root_dir    = r"D:\quan_ly_tai_nguyen_bien\data"                    # Thư mục chứa 10 vùng
output_dir  = r"D:\quan_ly_tai_nguyen_bien\dataset\data_cleaned_columns"            # TẤT CẢ FILE VÀO ĐÂY

# Tạo thư mục đầu ra nếu chưa có
os.makedirs(output_dir, exist_ok=True)

# Ánh xạ cột: tên gốc → tên mới (tiếng Việt, theo yêu cầu mới)
COLUMN_MAPPING = {
    "Dates":                                   "thoi_gian",
    "Salinity (psu)":                          "do_man",             # Độ mặn
    "pH":                                      "ph",                 # pH
    "Ammonia Nitrogen (mg/L)":                 "nh3",                # NH3 (Ammonia Nitrogen)
    "Temperature (°C)":                        "nhiet_do_nuoc",      # Nhiệt độ nước biển
    "5-day Biochemical Oxygen Demand (mg/L)":  "bod5",               # BOD5
    "Suspended Solids (mg/L)":                 "tss",                # TSS
    "Arsenic (mg/kg)":                         "as",                 # Asen (trầm tích)
    "Cadmium (mg/kg)":                         "cd",                 # Cadmi (trầm tích)
    "Lead (mg/kg)":                            "pb",                 # Chì (trầm tích)
    "Copper (mg/kg)":                          "cu",                 # Đồng (trầm tích)
    "Zinc (mg/kg)":                            "zn",                 # Kẽm (trầm tích)
}

print("BẮT ĐẦU LỌC & ĐỔI TÊN CỘT – LƯU VÀO 1 THƯ MỤC DUY NHẤT")
print("=" * 80)

processed = 0

for subdir in os.listdir(root_dir):
    subdir_path = os.path.join(root_dir, subdir)
    if not os.path.isdir(subdir_path):
        continue
    
    input_csv = os.path.join(subdir_path, "merged.csv")
    if not os.path.exists(input_csv):
        print(f"[BỎ QUA] Không tìm thấy merged.csv → {subdir}")
        continue

    try:
        df = pd.read_csv(input_csv, low_memory=False)
        print(f"Đang xử lý: {subdir:<35} → {len(df):,} dòng", end="")

        # Tìm các cột thực tế tồn tại trong file
        cols_to_keep = []
        rename_dict = {}

        for orig_name, new_name in COLUMN_MAPPING.items():
            if orig_name in df.columns:
                cols_to_keep.append(orig_name)
                rename_dict[orig_name] = new_name
            else:
                # Tìm gần đúng nếu tên cột hơi khác (ví dụ: có thêm khoảng trắng hoặc đơn vị)
                match = next((c for c in df.columns if orig_name.replace(" (mg/L)", "").replace(" (mg/kg)", "") in c), None)
                if match:
                    cols_to_keep.append(match)
                    rename_dict[match] = new_name

        if not cols_to_keep:
            print(" → Không tìm thấy cột nào khớp!")
            continue

        # Lọc và đổi tên
        df_clean = df[cols_to_keep].copy()
        df_clean.rename(columns=rename_dict, inplace=True)

        # Bổ sung cột bổ sung nếu có (station, depth)
        if "Station" in df.columns:
            df_clean["station"] = df["Station"]
        if "Depth" in df.columns:
            df_clean["do_sau"] = df["Depth"]

        # Lưu file với tên vùng
        output_file = os.path.join(output_dir, f"{subdir}.csv")
        df_clean.to_csv(output_file, index=False, encoding="utf-8-sig")

        print(f" → DONE → {os.path.basename(output_file)} ({len(df_clean.columns)} cột)")
        processed += 1

    except Exception as e:
        print(f" → LỖI: {e}")

# ==================== HOÀN TẤT ====================
print("=" * 80)
print(f"HOÀN TẤT! Đã xử lý thành công {processed} vùng")
print(f"Tất cả file đã được lưu vào thư mục duy nhất:")
print(f"   → {output_dir}")
print("\nDanh sách file kết quả:")
for f in sorted(os.listdir(output_dir)):
    if f.endswith(".csv"):
        print(f"   • {f}")
print("\nBạn có thể gộp tất cả file này bằng pandas nếu cần (ví dụ: pd.concat).")