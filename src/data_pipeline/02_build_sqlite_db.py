import os
import sqlite3
import pandas as pd

RAW_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "raw")
PROCESSED_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "processed")
DB_PATH = os.path.join(PROCESSED_DATA_DIR, "clinical_data.db")

def build_database():
    """Loads CSV files from raw data directory and creates a SQLite database."""
    os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)
    
    # Remove existing db if it exists
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print("Removed existing database.")

    try:
        conn = sqlite3.connect(DB_PATH)
        print(f"Connected to SQLite database at {DB_PATH}")

        # Iterate through all CSVs in raw directory
        for filename in os.listdir(RAW_DATA_DIR):
            if filename.endswith(".csv"):
                table_name = filename.replace(".csv", "")
                csv_path = os.path.join(RAW_DATA_DIR, filename)
                
                print(f"Loading {filename} into table '{table_name}'...")
                df = pd.read_csv(csv_path)
                
                # Write data to SQLite, replacing if exists
                # USUBJID will be present in these SDTM tables
                df.to_sql(table_name, conn, if_exists='replace', index=False)
                
                # Create an index on USUBJID if the column exists
                if 'USUBJID' in df.columns:
                    cursor = conn.cursor()
                    cursor.execute(f"CREATE INDEX idx_{table_name}_usubjid ON {table_name} (USUBJID)")
                    print(f"Created index on USUBJID for table '{table_name}'.")

        print("Database construction complete.")

    except Exception as e:
        print(f"An error occurred while building the database: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    build_database()
