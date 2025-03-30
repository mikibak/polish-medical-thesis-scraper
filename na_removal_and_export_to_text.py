import pandas as pd

# Load the doctorates.csv file
df = pd.read_csv('./doctorates_with_text_2.csv', sep='|')

## Remove rows with missing text
df = df.dropna(subset=['Text'])

#saving each df['Text'] in a txt file not based on index
for i in range(len(df)):
    with open(f"./text_files/doctorates_2_doc{i}.txt", "w", encoding="utf-8") as file:
        file.write(str(df['Text'][i]))

df.drop(columns=['Text'], inplace=True)
df.to_csv('./doctorates_licenses_and_file_links/doctorates_links_2.csv', sep='|', index=False)

