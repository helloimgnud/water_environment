import os
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter, AutoDateLocator

# ==================== CẤU HÌNH ====================
base_dir = r"D:\quan_ly_tai_nguyen_bien\dataset\data_split_vertical"

folders = {
    "01_SEDIMENT_SAMPLES": {
        "desc": "Trầm tích",
        "cols": ['as', 'cd', 'pb', 'cu', 'zn'],  # 5 cột
        "subplot_rows": 2,
        "subplot_cols": 3
    },
    "03_WATER_QUALITY_SAMPLES_SURFACE_WATER": {
        "desc": "Surface Water",
        "cols": ['do_man', 'ph', 'nh3', 'nhiet_do_nuoc', 'bod5', 'tss'],  # 6 cột
        "subplot_rows": 2,
        "subplot_cols": 3
    },
    "04_WATER_QUALITY_SAMPLES_MIDDLE_WATER": {
        "desc": "Middle Water",
        "cols": ['do_man', 'ph', 'nh3', 'nhiet_do_nuoc', 'bod5', 'tss'],  # 6 cột
        "subplot_rows": 2,
        "subplot_cols": 3
    },
    "05_WATER_QUALITY_SAMPLES_BOTTOM_WATER": {
        "desc": "Bottom Water",
        "cols": ['do_man', 'ph', 'nh3', 'nhiet_do_nuoc', 'bod5', 'tss'],  # 6 cột
        "subplot_rows": 2,
        "subplot_cols": 3
    }
}

print("BẮT ĐẦU VẼ BIỂU ĐỒ CHO CÁC CHỈ SỐ THEO THỜI GIAN")
print("=" * 80)

processed_files = 0

for folder_name, config in folders.items():
    folder_path = os.path.join(base_dir, folder_name)
    print(f"\nXỬ LÝ FOLDER: {folder_name} ({config['desc']})")
    
    for root, dirs, files in os.walk(folder_path):
        for filename in files:
            if not filename.lower().endswith(".csv"):
                continue
            
            filepath = os.path.join(root, filename)
            rel_path = os.path.relpath(filepath, base_dir)
            print(f" → File: {rel_path}")
            
            try:
                df = pd.read_csv(filepath, low_memory=False)
                
                if 'thoi_gian' not in df.columns:
                    print("   → Bỏ qua: Không có cột 'thoi_gian'")
                    continue
                
                df['thoi_gian'] = pd.to_datetime(df['thoi_gian'], errors='coerce')
                df = df.dropna(subset=['thoi_gian'])  # Bỏ dòng thiếu thời gian
                
                if df.empty:
                    print("   → Bỏ qua: Dataset rỗng sau xử lý thời gian")
                    continue
                
                # Thiết lập subplot
                rows = config['subplot_rows']
                cols = config['subplot_cols']
                fig, axes = plt.subplots(rows, cols, figsize=(15, 10))  # Kích thước lớn để tránh chồng chéo
                axes = axes.flatten()  # Biến thành mảng 1D để dễ loop
                
                plot_count = 0
                
                for col in config['cols']:
                    if col not in df.columns:
                        continue
                    
                    # Lọc dữ liệu không null cho cột này
                    plot_df = df[[ 'thoi_gian', col ]].dropna(subset=[col])
                    
                    if plot_df.empty:
                        axes[plot_count].set_title(f"{col} (Không có dữ liệu)")
                        plot_count += 1
                        continue
                    
                    # Tính min/max cho trục y
                    y_min = plot_df[col].min() * 0.95 if plot_df[col].min() > 0 else plot_df[col].min() * 1.05
                    y_max = plot_df[col].max() * 1.05
                    
                    # Tính min/max thời gian
                    x_min = plot_df['thoi_gian'].min()
                    x_max = plot_df['thoi_gian'].max()
                    
                    # Vẽ line plot
                    axes[plot_count].plot(plot_df['thoi_gian'], plot_df[col], marker='o', linestyle='-', markersize=4)
                    axes[plot_count].set_title(col, fontsize=12)
                    axes[plot_count].set_xlabel('Thời gian', fontsize=10)
                    axes[plot_count].set_ylabel(col, fontsize=10)
                    axes[plot_count].set_ylim(y_min, y_max)
                    axes[plot_count].set_xlim(x_min, x_max)
                    
                    # Định dạng trục x (thời gian)
                    axes[plot_count].xaxis.set_major_locator(AutoDateLocator())
                    axes[plot_count].xaxis.set_major_formatter(DateFormatter('%Y-%m'))
                    axes[plot_count].tick_params(axis='x', rotation=45)
                    
                    axes[plot_count].grid(True)
                    plot_count += 1
                
                # Ẩn subplot thừa nếu có (ví dụ: sediment chỉ 5 cột, subplot 6)
                for i in range(plot_count, len(axes)):
                    axes[i].axis('off')
                
                # Căn chỉnh tổng thể
                fig.suptitle(f"Biểu đồ chỉ số theo thời gian - {filename}", fontsize=16)
                plt.tight_layout(rect=[0, 0.03, 1, 0.95])  # Tránh chồng chéo
                plt.subplots_adjust(hspace=0.4, wspace=0.3)
                
                # Lưu ảnh vào chính folder chứa file
                plot_filename = f"{os.path.splitext(filename)[0]}_indicators_plot.png"
                plot_path = os.path.join(root, plot_filename)
                plt.savefig(plot_path, dpi=300, bbox_inches='tight')
                plt.close(fig)  # Đóng figure để tiết kiệm bộ nhớ
                
                print(f"   → Đã lưu biểu đồ: {plot_filename}")
                
                processed_files += 1

            except Exception as e:
                print(f"   → LỖI: {e}")

print("=" * 80)
print(f"HOÀN TẤT! Đã xử lý {processed_files} file")
print("Mỗi biểu đồ được lưu vào chính folder chứa dataset (tên: <filename>_indicators_plot.png)")
print("Biểu đồ dùng subplot 2x3, tự động điều chỉnh min/max, không chồng chéo.")