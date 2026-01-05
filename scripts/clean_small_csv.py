import os
import csv
from datetime import datetime

# ================== CONFIG ==================
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(PROJECT_ROOT, "data_cleaned")
LOG_DIR = os.path.join(PROJECT_ROOT, "log")
LOG_FILE = os.path.join(LOG_DIR, "clean_csv.log")

MIN_ROWS = 100
DRY_RUN = False  # True: chỉ log, False: xóa thật
# ============================================


def count_csv_rows(file_path):
    """
    Đếm số dòng dữ liệu trong file CSV.
    Không tính header.
    """
    try:
        with open(file_path, newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            rows = list(reader)
            if len(rows) <= 1:
                return 0
            return len(rows) - 1
    except Exception:
        return -1


def write_log(message):
    with open(LOG_FILE, "a", encoding="utf-8") as log:
        log.write(message + "\n")


def main():
    os.makedirs(LOG_DIR, exist_ok=True)

    start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    write_log("=" * 60)
    write_log(f"Start scan at {start_time}")
    write_log(f"Dry run mode: {DRY_RUN}")
    write_log(f"Minimum rows required: {MIN_ROWS}")

    for root, _, files in os.walk(DATA_DIR):
        for file in files:
            if not file.lower().endswith(".csv"):
                continue

            file_path = os.path.join(root, file)
            row_count = count_csv_rows(file_path)

            if row_count == -1:
                write_log(f"[ERROR] Cannot read file: {file_path}")
                continue

            if row_count < MIN_ROWS:
                if DRY_RUN:
                    write_log(
                        f"[DRY RUN] File will be removed: {file_path} | rows={row_count}"
                    )
                else:
                    try:
                        os.remove(file_path)
                        write_log(
                            f"[REMOVED] {file_path} | rows={row_count}"
                        )
                    except Exception as e:
                        write_log(
                            f"[ERROR] Failed to remove {file_path} | {str(e)}"
                        )

    end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    write_log(f"Finished at {end_time}")
    write_log("=" * 60)


if __name__ == "__main__":
    main()
