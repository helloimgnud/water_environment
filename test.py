import os
import json
from prophet.serialize import model_from_json
import pandas as pd

# ===============================
# CẤU HÌNH ĐƯỜNG DẪN
# ===============================
FOLDER_PATH = "/home/duongnt/auto-hdr/test/prophet_models_sediment/Deep Bay/DS1"
OUTPUT_CSV = "/home/duongnt/auto-hdr/test/forecast_summary_DS1.csv"

# ===============================
# TÌM TẤT CẢ SUBFOLDER (CỘT)
# ===============================
subfolders = [
    f for f in os.listdir(FOLDER_PATH)
    if os.path.isdir(os.path.join(FOLDER_PATH, f))
]

if not subfolders:
    raise ValueError(f"Không tìm thấy subfolder nào trong {FOLDER_PATH}")

print(f"🔍 Tìm thấy {len(subfolders)} chỉ tiêu: {', '.join(subfolders)}")

# ===============================
# DỰ BÁO VÀ TỔNG HỢP
# ===============================
forecast_dfs = []

for element in sorted(subfolders):
    model_dir = os.path.join(FOLDER_PATH, element)
    model_path = os.path.join(model_dir, "prophet_model.json")
    config_path = os.path.join(model_dir, "config.json")

    if not (os.path.exists(model_path) and os.path.exists(config_path)):
        print(f"⚠️ Bỏ qua {element}: Thiếu file model hoặc config")
        continue

    print(f"\n🔬 Load model cho {element.upper()}")

    # Load config
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    cap_value = config.get("cap_value")     # None nếu linear
    floor_value = config.get("floor_value", 0.0)

    # Load model
    with open(model_path, "r", encoding="utf-8") as fin:
        model = model_from_json(fin.read())

    # Tạo future dataframe
    future = model.make_future_dataframe(periods=12, freq="M")

    if cap_value is not None:
        future["cap"] = cap_value
        future["floor"] = floor_value
        print(f"   → Logistic growth (cap={cap_value:.4f}, floor={floor_value})")
    else:
        print("   → Linear growth")

    forecast = model.predict(future)

    # ===============================
    # LẤY 12 THÁNG TƯƠNG LAI – CHỈ GIỮ yhat
    # ===============================
    future_forecast = forecast.tail(12)[["ds", "yhat"]].copy()
    future_forecast["element"] = element.lower()

    forecast_dfs.append(future_forecast)

# ===============================
# TỔNG HỢP DATAFRAME
# ===============================
if not forecast_dfs:
    raise ValueError("Không có dự báo nào được tạo!")

df_summary = pd.concat(forecast_dfs, ignore_index=True)

# Pivot: mỗi chỉ tiêu là một cột
df_summary = df_summary.pivot(
    index="ds",
    columns="element",
    values="yhat"
)

# Reset index
df_summary.reset_index(inplace=True)

# ===============================
# XỬ LÝ THỜI GIAN
# ===============================
# Đổi tên ds → thoi_gian
df_summary.rename(columns={"ds": "thoi_gian"}, inplace=True)

# Gán ngày cố định là 28
df_summary["thoi_gian"] = (
    pd.to_datetime(df_summary["thoi_gian"])
    .dt.to_period("M")
    .dt.to_timestamp()
    + pd.offsets.Day(27)
)

# Format YYYY-MM-DD
df_summary["thoi_gian"] = df_summary["thoi_gian"].dt.strftime("%Y-%m-%d")

print("\n📊 DataFrame tổng hợp:")
print(df_summary.head())

# ===============================
# LƯU CSV
# ===============================
df_summary.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")

print(f"\n✅ Đã lưu CSV tại: {OUTPUT_CSV}")
print("🎉 Hoàn tất!")
