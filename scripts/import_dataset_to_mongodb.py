import os
import pandas as pd
from pymongo import MongoClient, ASCENDING
from dotenv import load_dotenv

# ==============================
# LOAD ENV
# ==============================
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("MONGO_DB", "marine_environment")

BASE_DATA_DIR = "data_cleaned"

# Folders to process (skip 02 since 03/04/05 are detailed versions)
FOLDERS_TO_PROCESS = [
    "01_SEDIMENT_SAMPLES",
    "03_WATER_QUALITY_SAMPLES_SURFACE_WATER",
    "04_WATER_QUALITY_SAMPLES_MIDDLE_WATER",
    "05_WATER_QUALITY_SAMPLES_BOTTOM_WATER",
]

# ==============================
# CONNECT MONGODB
# ==============================
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db["samples"]

# ==============================
# DROP EXISTING COLLECTION
# ==============================
print("Dropping existing 'samples' collection...")
collection.drop()
print("Collection dropped successfully!")

# ==============================
# HELPER FUNCTIONS
# ==============================
def detect_sample_info(folder_name):
    """
    Xác định loại mẫu & tầng nước từ tên folder
    - SEDIMENT: No water layer (None)
    - WATER_QUALITY: Has water layer (SURFACE/MIDDLE/BOTTOM)
    """
    if "SEDIMENT" in folder_name:
        return "SEDIMENT", None  # Sediment has no water layer
    elif "SURFACE_WATER" in folder_name:
        return "WATER_QUALITY", "SURFACE"
    elif "MIDDLE_WATER" in folder_name:
        return "WATER_QUALITY", "MIDDLE"
    elif "BOTTOM_WATER" in folder_name:
        return "WATER_QUALITY", "BOTTOM"
    else:
        return None, None


# ==============================
# MAIN IMPORT LOGIC
# ==============================
inserted_count = 0
skipped_duplicates = 0

for folder in FOLDERS_TO_PROCESS:
    folder_path = os.path.join(BASE_DATA_DIR, folder)
    
    if not os.path.exists(folder_path):
        print(f"Warning: Folder not found: {folder_path}")
        continue
    
    print(f"\nProcessing folder: {folder}")
    
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if not file.endswith(".csv"):
                continue

            file_path = os.path.join(root, file)

            # ------------------------------
            # Parse metadata from path
            # ------------------------------
            parts = file_path.split(os.sep)
            
            # data_cleaned / 03_WATER_QUALITY_SAMPLES_SURFACE_WATER / Mirs Bay / MS1.csv
            main_folder = parts[1]
            region = parts[2]
            station = file.replace(".csv", "")

            sample_type, water_layer = detect_sample_info(main_folder)

            # ------------------------------
            # Read CSV and remove duplicates
            # ------------------------------
            try:
                df = pd.read_csv(file_path)
                original_count = len(df)
                
                # Remove duplicate rows
                df = df.drop_duplicates()
                duplicates_removed = original_count - len(df)
                skipped_duplicates += duplicates_removed
                
                if duplicates_removed > 0:
                    print(f"  Removed {duplicates_removed} duplicates from {file}")
                    
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
                continue

            # ------------------------------
            # Insert each row as document
            # ------------------------------
            documents = []
            for _, row in df.iterrows():
                doc = {
                    "sample_type": sample_type,
                    "water_layer": water_layer,
                    "region": region,
                    "station": station,
                    "source_file": file,
                    "data": row.dropna().to_dict()
                }
                documents.append(doc)

            if documents:
                collection.insert_many(documents)
                inserted_count += len(documents)
                print(f"  Inserted {len(documents)} records from {file}")

# ==============================
# CREATE INDEXES
# ==============================
print("\n" + "="*50)
print("Creating indexes...")

# Index for common query patterns
collection.create_index([("sample_type", ASCENDING)], name="idx_sample_type")
collection.create_index([("water_layer", ASCENDING)], name="idx_water_layer")
collection.create_index([("region", ASCENDING)], name="idx_region")
collection.create_index([("station", ASCENDING)], name="idx_station")

# Compound index for common filter combinations
collection.create_index(
    [("sample_type", ASCENDING), ("region", ASCENDING), ("station", ASCENDING)],
    name="idx_type_region_station"
)

# Index for date queries (in nested data)
collection.create_index([("data.thoi_gian", ASCENDING)], name="idx_date")

print("Indexes created successfully!")

# List all indexes
print("\nCurrent indexes:")
for index in collection.list_indexes():
    print(f"  - {index['name']}: {index['key']}")

# ==============================
# SUMMARY
# ==============================
print("\n" + "="*50)
print("IMPORT COMPLETE!")
print(f"  Total documents inserted: {inserted_count:,}")
print(f"  Duplicates removed: {skipped_duplicates:,}")
print(f"  Collection: {DB_NAME}.samples")
print("="*50)
