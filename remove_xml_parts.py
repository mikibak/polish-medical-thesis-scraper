# Program for removing XML parts from the xml files scraped from the Polish Medical Thesis database.

import os
import re
import sys
import urllib.request as URL
import pandas as pd
import IPython.display as display
import subprocess

def remove_xml_parts(file_path, i):
    """Remove XML parts from the given XML file."""

    # save title of file
    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()

    # Step 1: Extract only the <p> content
    p_matches = re.findall(r'<p>(.*?)</p>', content, re.S)

    # Step 2: Remove any remaining XML tags inside the paragraphs
    clean_paragraphs = [re.sub(r'<[^>]+>', '', p).strip() for p in p_matches]

    # Step 3: Join the paragraphs into one text
    final_text = " ".join(clean_paragraphs)

    # Remove references to bibliography eg. "[35]"
    clean_text = re.sub(r'\[\d+\]', '', final_text)
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()

    df_doc["Text"][i] = clean_text


    print(f"XML parts removed from: {file_path}")

# Usage example
if __name__ == "__main__":
    df_doc = pd.read_csv("doctorates.csv")

    display.display(df_doc)

    for i in range(len(df_doc)):
        title = df_doc["Title"][i].replace(" ", "_")
        URL.urlretrieve(df_doc["File"][i], filename=f"{title}.pdf")
        subprocess.run(["python3", "-m", "grobid_client.grobid_client", "--input", "./", "--output", "./out/", "processFulltextDocument"])
        remove_xml_parts(f"./out/{title}.grobid.tei.xml", i)
        os.remove(f"{title}.pdf")
