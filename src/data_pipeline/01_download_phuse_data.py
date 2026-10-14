import os
import requests
import pandas as pd

BASE_URL = "https://raw.githubusercontent.com/phuse-org/phuse-scripts/master/data/sdtm/TDF_SDTM_v1.0/"
DATASETS = ["dm", "ae", "cm", "mh", "lb", "ex"]
RAW_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "raw")

def download_and_convert_dataset(dataset_name: str):
    """Downloads a .xpt dataset from PHUSE and converts it to CSV."""
    xpt_url = f"{BASE_URL}{dataset_name}.xpt"
    xpt_filepath = os.path.join(RAW_DATA_DIR, f"{dataset_name}.xpt")
    csv_filepath = os.path.join(RAW_DATA_DIR, f"{dataset_name}.csv")

    try:
        print(f"Downloading {dataset_name}.xpt...")
        response = requests.get(xpt_url)
        response.raise_for_status()

        with open(xpt_filepath, "wb") as f:
            f.write(response.content)

        print(f"Converting {dataset_name}.xpt to CSV...")
        # Use pandas to read SAS transport file
        df = pd.read_sas(xpt_filepath, format='xport')
        
        # Decode byte strings to standard strings (common in xpt files)
        for col in df.columns:
            if df[col].dtype == object:
                try:
                    df[col] = df[col].str.decode('utf-8')
                except Exception:
                    pass

        df.to_csv(csv_filepath, index=False)
        print(f"Successfully saved {dataset_name}.csv")
        
    except requests.exceptions.RequestException as e:
        print(f"Failed to download {dataset_name}: {e}")
    except Exception as e:
        print(f"Error processing {dataset_name}: {e}")
    finally:
        # Clean up the intermediate .xpt file if it exists
        if os.path.exists(xpt_filepath):
            os.remove(xpt_filepath)

def main():
    os.makedirs(RAW_DATA_DIR, exist_ok=True)
    print(f"Downloading datasets to {RAW_DATA_DIR}...")
    for ds in DATASETS:
        download_and_convert_dataset(ds)
    print("Download and conversion complete.")

if __name__ == "__main__":
    main()
