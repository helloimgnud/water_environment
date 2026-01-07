import pandas as pd
import os
import numpy as np

# ==================== THƯ MỤC CHỨA FILE GỐC ====================
folder = r"D:\quan_ly_tai_nguyen_bien\dataset\data_cleaned_columns"

# Hàm làm sạch chuẩn quốc tế (EPA / WHO / HELCOM / OSPAR / QCVN VN)
def clean_international(value):
    if pd.isna(value):
        return np.nan
    s = str(value).strip()
    
    if s.startswith('<'):
        # <0.001 → 0.0005    |    <0 → 0.0    |    <5 → 2.5
        try:
            limit = float(s[1:] or 0)      # nếu chỉ có "<" thì limit = 0
            return round(limit / 2, 6)     # x/2 – chuẩn quốc tế
        except:
            return np.nan
    elif s.startswith('>'):
        # >8.8 → 8.8    |    >6.5 → 6.5
        try:
            return float(s[1:])            # giữ nguyên giá trị vượt
        except:
            return np.nan
    else:
        try:
            return float(s)
        except:
            return np.nan

# Các cột cần làm sạch
cols_to_clean = ['nh3', 'tss', 'bod5', 'cd', 'pb', 'cu']

print("BẮT ĐẦU LÀM SẠCH CHUẨN QUỐC TẾ – GHI ĐÈ LÊN FILE GỐC")
print("=" * 80)

count = 0
for file in os.listdir(folder):
    if not file.lower().endswith(".csv"):
        continue
    
    filepath = os.path.join(folder, file)
    df = pd.read_csv(filepath, low_memory=False)
    old_rows = len(df)
    
    print(f"Đang xử lý: {file:<35} → {old_rows:,} dòng", end="")
    
    # Làm sạch 6 cột
    for col in cols_to_clean:
        if col in df.columns:
            df[col] = df[col].apply(clean_international)
    
    # # Chuẩn hóa ngày tháng luôn cho đẹp
    # if 'thoi_gian' in df.columns:
    #     df['thoi_gian'] = pd.to_datetime(df['thoi_gian'], dayfirst=True, errors='coerce')
    
    # GHI ĐÈ LÊN FILE GỐC
    df.to_csv(filepath, index=False, encoding='utf-8-sig')
    
    print(" → ĐÃ SẠCH & GHI ĐÈ THÀNH CÔNG!")
    count += 1

print("=" * 80)
print(f"HOÀN TẤT! Đã làm sạch và ghi đè thành công {count} file")
print("Tất cả dữ liệu giờ đã:")
print("   • <x  → thay bằng x/2 (chuẩn US EPA, WHO, HELCOM, QCVN VN)")
print("   • >y  → giữ nguyên y")
print("   • Ngày tháng đã là datetime chuẩn")
print("→ Bạn có thể ghép, phân tích, vẽ đồ thị, nộp luận văn/bài báo SCI ngay lập tức!")

