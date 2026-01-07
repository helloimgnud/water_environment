import os
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# ==================== CẤU HÌNH ====================
base_dir = r"D:\quan_ly_tai_nguyen_bien\dataset\data_outliers_as_nan"

folders = {
    "01_SEDIMENT_SAMPLES": {
        "desc": "Trầm tích",
        "cols": ['as', 'cd', 'pb', 'cu', 'zn']  # Các cột số để tính tương quan
    },
    "03_WATER_QUALITY_SAMPLES_SURFACE_WATER": {
        "desc": "Surface Water",
        "cols": ['do_man', 'ph', 'nh3', 'nhiet_do_nuoc', 'bod5', 'tss']
    },
    "04_WATER_QUALITY_SAMPLES_MIDDLE_WATER": {
        "desc": "Middle Water",
        "cols": ['do_man', 'ph', 'nh3', 'nhiet_do_nuoc', 'bod5', 'tss']
    },
    "05_WATER_QUALITY_SAMPLES_BOTTOM_WATER": {
        "desc": "Bottom Water",
        "cols": ['do_man', 'ph', 'nh3', 'nhiet_do_nuoc', 'bod5', 'tss']
    }
}

print("BẮT ĐẦU VẼ BIỂU ĐỒ TƯƠNG QUAN PEARSON/SPEARMAN CHO CÁC CHỈ SỐ")
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
                
                # Chọn các cột số từ config
                cols = [col for col in config['cols'] if col in df.columns]
                if len(cols) < 2:
                    print("   → Bỏ qua: Không đủ cột số để tính tương quan (cần ít nhất 2 cột)")
                    continue
                
                df_numeric = df[cols].dropna()  # Bỏ dòng có NaN để tính tương quan chính xác
                
                if df_numeric.empty or len(df_numeric) < 2:
                    print("   → Bỏ qua: Không đủ dữ liệu hợp lệ để tính tương quan")
                    continue
                
                # Tính ma trận tương quan Pearson
                corr_pearson = df_numeric.corr(method='pearson')
                
                # Tính ma trận tương quan Spearman
                corr_spearman = df_numeric.corr(method='spearman')
                
                # Thiết lập figure với 2 subplot (bên trái Pearson, bên phải Spearman)
                fig, axes = plt.subplots(1, 2, figsize=(16, 8))
                
                # Vẽ heatmap Pearson
                sns.heatmap(corr_pearson, ax=axes[0], annot=True, fmt=".2f", cmap='coolwarm', vmin=-1, vmax=1, square=True, linewidths=0.5)
                axes[0].set_title('Tương quan Pearson')
                
                # Vẽ heatmap Spearman
                sns.heatmap(corr_spearman, ax=axes[1], annot=True, fmt=".2f", cmap='coolwarm', vmin=-1, vmax=1, square=True, linewidths=0.5)
                axes[1].set_title('Tương quan Spearman')
                
                # Căn chỉnh tổng thể
                fig.suptitle(f"Biểu đồ Tương quan - {filename}", fontsize=16)
                plt.tight_layout(rect=[0, 0.03, 1, 0.95])
                
                # Lưu biểu đồ vào chính folder chứa file
                plot_filename = f"{os.path.splitext(filename)[0]}_correlation_plot.png"
                plot_path = os.path.join(root, plot_filename)
                plt.savefig(plot_path, dpi=300, bbox_inches='tight')
                plt.close(fig)  # Đóng figure để tiết kiệm bộ nhớ
                
                print(f"   → Đã lưu biểu đồ: {plot_filename}")
                
                processed_files += 1

            except Exception as e:
                print(f"   → LỖI: {e}")

print("=" * 80)
print(f"HOÀN TẤT! Đã xử lý {processed_files} file")
print("Mỗi biểu đồ (Pearson + Spearman) được lưu vào chính folder chứa dataset (tên: <filename>_correlation_plot.png)")
print("Biểu đồ dùng heatmap với annot để hiển thị giá trị tương quan rõ ràng.")