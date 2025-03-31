#Divide the file_links.csv file into smaller files for easier processing.

import pandas as pd

# Load the file_links.csv file
df = pd.read_csv("scraper/file_links.csv")

# Split the data into chunks of 250 rows each
chunks = [df.iloc[i:i+250] for i in range(0, len(df), 250)]

# Save each chunk to a separate CSV file
for i, chunk in enumerate(chunks):
    chunk.to_csv(f"doctorates_{i+1}.csv", index=False)

print(f"Data divided into {len(chunks)} files.")