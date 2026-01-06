import os
import json
from prophet.serialize import model_from_json
import pandas as pd
import numpy as np  # ← THÊM IMPORT NÀY

def get_forecast_df(type_indicator, area, station):
    """
    Hàm dự báo 12 tháng cho tất cả các chỉ tiêu của một trạm cụ thể.
    
    Args:
        type_indicator (str): 'Sediment', 'Water_Surface', 'Water_Middle', hoặc 'Water_Bottom'
        area (str): Tên khu vực (tên folder khu vực)
        station (str): Tên trạm (tên folder trạm)
    
    Returns:
        pd.DataFrame: DataFrame chứa dự báo, với cột 'thoi_gian' và các cột chỉ tiêu (giá trị yhat đã inverse nếu cần).
    """
    BASE_DIR = r"../models"  # thay base_dir nếu cần
    
    # Xác định thư mục gốc dựa trên type_indicator
    if type_indicator == 'Sediment':
        root_folder = 'prophet_models_sediment'
    elif type_indicator in ['Water_Surface', 'Water_Middle', 'Water_Bottom']:
        root_folder = f"prophet_models_{type_indicator.lower()}"
    else:
        raise ValueError("type_indicator phải là 'Sediment', 'Water_Surface', 'Water_Middle' hoặc 'Water_Bottom'")
    
    # Đường dẫn đầy đủ đến folder trạm
    FOLDER_PATH = os.path.join(BASE_DIR, root_folder, area, station)
    
    if not os.path.exists(FOLDER_PATH):
        raise FileNotFoundError(f"Không tìm thấy folder trạm: {FOLDER_PATH}")
    
    print(f" Đang xử lý: {type_indicator} | Khu vực: {area} | Trạm: {station}")
    
    # Xác định có cần inverse log transform không
    requires_inverse_log = type_indicator in ['Water_Surface', 'Water_Middle', 'Water_Bottom']
    transform_note = " (sẽ áp dụng expm1)" if requires_inverse_log else " (scale gốc)"
    print(f"   → Chế độ dự báo:{transform_note}")
    
    # Tìm tất cả subfolder (các chỉ tiêu)
    subfolders = [f for f in os.listdir(FOLDER_PATH) if os.path.isdir(os.path.join(FOLDER_PATH, f))]
    
    if not subfolders:
        raise ValueError(f"Không tìm thấy chỉ tiêu nào trong {FOLDER_PATH}")
    
    print(f"   → Tìm thấy {len(subfolders)} chỉ tiêu: {', '.join(sorted(subfolders))}")
    
    forecast_dfs = []
    
    for element in sorted(subfolders):
        model_dir = os.path.join(FOLDER_PATH, element)
        model_path = os.path.join(model_dir, "prophet_model.json")
        config_path = os.path.join(model_dir, "config.json")
        
        if not (os.path.exists(model_path) and os.path.exists(config_path)):
            print(f"     Bỏ qua {element.upper()}: Thiếu model hoặc config")
            continue
        
        # Load config
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        
        cap_value = config.get("cap_value")
        floor_value = config.get("floor_value", 0.0)
        
        # Load model
        with open(model_path, "r", encoding="utf-8") as fin:
            model = model_from_json(fin.read())
        
        # Tạo future dataframe
        future = model.make_future_dataframe(periods=12, freq="M")
        
        if cap_value is not None:
            future["cap"] = cap_value
            future["floor"] = floor_value
            growth_type = "Logistic"
        else:
            growth_type = "Linear"
        
        print(f"   → {element.upper():<12} | {growth_type} growth", end="")
        if requires_inverse_log:
            print(" → expm1 sẽ được áp dụng")
        else:
            print("")
        
        forecast = model.predict(future)
        
        # Lấy 12 tháng tương lai
        future_forecast = forecast.tail(12)[["ds", "yhat"]].copy()
        
        # === QUAN TRỌNG: INVERSE LOG TRANSFORM NẾU LÀ WATER ===
        if requires_inverse_log:
            future_forecast["yhat"] = np.expm1(future_forecast["yhat"])
        
        future_forecast["element"] = element.lower()
        forecast_dfs.append(future_forecast)
    
    if not forecast_dfs:
        raise ValueError("Không có dự báo nào được tạo thành công!")
    
    # Tổng hợp
    df_summary = pd.concat(forecast_dfs, ignore_index=True)
    
    # Pivot: mỗi chỉ tiêu là một cột
    df_summary = df_summary.pivot(index="ds", columns="element", values="yhat")
    
    # Reset index và xử lý thời gian
    df_summary.reset_index(inplace=True)
    df_summary.rename(columns={"ds": "thoi_gian"}, inplace=True)
    
    # Chuyển thành ngày 28 của tháng
    df_summary["thoi_gian"] = (
        pd.to_datetime(df_summary["thoi_gian"])
        .dt.to_period("M")
        .dt.to_timestamp()
        + pd.offsets.Day(27)  # ngày 28
    )
    df_summary["thoi_gian"] = df_summary["thoi_gian"].dt.strftime("%Y-%m-%d")
    
    # Sắp xếp cột: thoi_gian đầu tiên, các chỉ tiêu theo alphabet
    cols = ['thoi_gian'] + sorted([col for col in df_summary.columns if col != 'thoi_gian'])
    df_summary = df_summary[cols]
    
    return df_summary


# ===============================
# HÀM MAIN ĐỂ TEST
# ===============================
def main():
    # Ví dụ test – thay đổi 3 tham số này để thử
    type_indicator = "Water_Surface"   # Thử đổi thành "Sediment" để thấy khác biệt
    area           = "Deep Bay"
    station        = "DM2"
    
    try:
        df = get_forecast_df(type_indicator, area, station)
        
        print("\n" + "="*80)
        print(" DỰ BÁO THÀNH CÔNG!")
        print(f"   Trạm: {station} ({type_indicator} - {area})")
        print(f"   Dự báo 12 tháng tương lai (ngày 28 hàng tháng)")
        if type_indicator in ['Water_Surface', 'Water_Middle', 'Water_Bottom']:
            print("   → Đã áp dụng inverse log transform (expm1)")
        else:
            print("   → Dự báo trên scale gốc (không transform)")
        print("="*80)
        print(df.round(3))  # Làm tròn để dễ đọc
        print("="*80)
        
        # Lưu CSV
        output_csv = f"forecast_{type_indicator}_{area}_{station}.csv"
        df.to_csv(output_csv, index=False, encoding="utf-8-sig")
        print(f" Đã lưu CSV tại: {output_csv}")
        
    except Exception as e:
        print(f" Lỗi: {e}")


if __name__ == "__main__":
    main()