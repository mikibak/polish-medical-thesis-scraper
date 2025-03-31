# Program for removing XML parts from the xml files scraped from the Polish Medical Thesis database.

import os
import re
import shutil
import socket
import sys
import time
import urllib.request as URL
import pandas as pd
import IPython.display as display
import subprocess
from PyPDF2 import PdfReader, PdfWriter
from concurrent.futures import ThreadPoolExecutor


def is_pdf_valid(file_path):
    try:
        with open(file_path, 'rb') as f:
            reader = PdfReader(f)
            _ = reader.pages[0]
        return True
    except Exception as e:
        return False

def remove_xml_parts(file_path):
    """Remove XML parts from the given XML file."""

    # save title of file
    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()

    # remove all citations and references in <ref> tags (and whitespaces in front of them)
    content = re.sub(r'<ref[^>]*/>', '', content, flags=re.S)
    content = re.sub(r'<ref[^>]*>.*?</ref>', '', content, flags=re.S)
    content = re.sub(r'<div[^>]*><head>Spis .*?/div>', '', content, flags=re.S)
    content = re.sub(r'<p[^>]*>Tabela.*?/div>', '</div>>', content, flags=re.S)

    # Step 1: Extract only the <p> content
    p_matches = re.findall(r'<p>(.*?)</p>', content, re.S)

    # Step 2: Remove any remaining XML tags inside the paragraphs
    clean_paragraphs = [re.sub(r'<[^>]+>', '', p).strip() for p in p_matches]

    # Step 3: Join the paragraphs into one text
    final_text = " ".join(clean_paragraphs)

    # Remove references to bibliography eg. "[35]"
    clean_text = re.sub(r'\[\d+\]', '', final_text)
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()
    return clean_text


def doctorate_execute(doc, i):
    print("Processing document ", i + 1, "/", len(doc))
    title = re.sub(r'[<>:"/\\|?*]', '_', doc["Title"][i])
    title = re.sub(r'\s+', ' ', title).strip().replace(' ', '_')[:255]

    try:
        if not os.path.exists(f"doct/{title}/doc.grobid.tei.xml"):
            try:
                os.makedirs(f"doct/{title}")
            except FileExistsError:
                pass

            if not is_pdf_valid(f"doct/{title}/doc.pdf"):
                try:
                    print(f"pdf {title} download")
                    URL.urlretrieve(doc["File"][i], filename=f"doct/{title}/doc.pdf")
                except Exception as e:
                    print(f"url error: {e}")

            try:
                subprocess.run(
                    [sys.executable, "-m", "grobid_client.grobid_client", "--input", f".\\doct\\{title}",
                     "processFulltextDocument"],
                    cwd=os.getcwd())
            except Exception as e:
                print(f"grobid error: {e}")

            if not is_pdf_valid(f"doct/{title}/doc.pdf"):
                print(f"pdf {title} is not valid")
                shutil.rmtree(f"doct/{title}")

        else:
            print(f"xml {title} exists")
    except Exception as e:
        print(f"??? {e}")


    print(f"Processing {title}.grobid.tei.xml")
    doc.at[i, "Text"] = remove_xml_parts(f"doct/{title}/doc.grobid.tei.xml")


# Usage example
if __name__ == "__main__":
    socket.setdefaulttimeout(60)

    df_doc = pd.read_csv("./Smaller_Files/doctorates_1.csv")

    display.display(df_doc)
    doctorate_count = len(df_doc)

    if not len(next(os.walk('doct'))[1]) < df_doc['Title'].nunique():
        exit(0)

    timeout_counter = 5
    while timeout_counter > 0:
        timeout_counter -= 1
        with ThreadPoolExecutor() as executor:
            executor.map(lambda i: doctorate_execute(df_doc, i), range(doctorate_count))

    df_doc = df_doc.dropna(subset=["Text"])
    df_doc.to_csv("doctorates_with_text_1.csv", sep='|', index=False)
