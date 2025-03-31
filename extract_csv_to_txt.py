import os
import pandas as pd
import glob

# Define input paths
metadata_file = "scraper/doctorates_metadata.csv"
text_files_pattern = "doctorates_with_text_*.csv"
output_dir = "extracted_texts"

# Ensure output directory exists
os.makedirs(output_dir, exist_ok=True)

# Load metadata and create a URL-to-ID mapping
metadata_df = pd.read_csv(metadata_file)
url_to_id = dict(zip(metadata_df["URL"], metadata_df["ID"]))

# Process all text CSV files
for file in glob.glob(text_files_pattern):
    df = pd.read_csv(file, delimiter="|")  # Assuming '|' as delimiter

    for _, row in df.iterrows():
        url = row["URL"]
        text = row["Text"]

        # Get ID from metadata using URL
        doc_id = url_to_id.get(url)
        if doc_id:
            filename = f"{output_dir}/{doc_id}.txt"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(str(text))

print("Text extraction completed.")
