# Program for removing XML parts from the xml files scraped from the Polish Medical Thesis database.
import glob
import os
import re
import shutil
import socket
import sys
import urllib.request as URL
import pandas as pd
import IPython.display as display
import subprocess
from PyPDF2 import PdfReader
from concurrent.futures import ThreadPoolExecutor
import spacy
from spacy.cli import download
from spacy.language import Language
from spacy_langdetect import LanguageDetector

@Language.factory("language_detector")
def create_language_detector(nlp, name):
    return LanguageDetector()

def filters_list(text):
    doc = nlp(text)
    return (doc._.language['language'] == "pl" and
        doc.cats["Other"] > 0.40)


def filter_paragraphs(paragraphs):
    filtered_text = " ".join([f'{p}\n' for p in paragraphs if filters_list(p)])
    return filtered_text

def filter_sentences(paragraphs):
    text = (" ".join(paragraphs)).split(". ")
    filtered_text = "".join([f"{s}. " for s in text if filters_list(s)])
    return filtered_text

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
    content = re.sub(r'<p[^>]*>Tabela.*?/div>', '</div>>', content, flags=re.S)

    # Step 1: Extract only the <p> content
    p_matches = re.findall(r'<p>(.*?)</p>', content, re.S)

    # Step 2: Remove any remaining XML tags inside the paragraphs
    clean_paragraphs = [re.sub(r'<[^>]+>', '', p).strip() for p in p_matches]

    # Step 3: Remove fragments in English and join the paragraphs into one text
    final_text = filter_sentences(clean_paragraphs)

    # Remove "Downloaded" sentence
    clean_text = re.sub(r'Pobrano z .*?/ Downloaded from Repository of Polish Platform of Medical Research .*? ', '', final_text)

    # Remove multi dots
    clean_text = re.sub(r'\.{4,}', '', clean_text)

    # Remove references to bibliography eg. "[35]"
    clean_text = re.sub(r'\[\d+\]', '', clean_text)
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

            try:
                subprocess.run(
                    [sys.executable, "-m", "grobid_client.grobid_client", "--input", f".\\doct\\{title}",
                     "processFulltextDocument"],
                    cwd=os.getcwd())
            except Exception as e:
                print(f"grobid error: {e}")

            if not is_pdf_valid(f"doct/{title}/doc.pdf"):
                print(f"{title}.pdf is not valid")
                shutil.rmtree(f"doct/{title}")

        else:
            print(f"{title}.grobid.tei.xml exists")
    except Exception as e:
        print(f"??? {e}")

    if not os.path.exists(f"output/{title}.txt"):
        try:
            os.mkdir(f"output")
        except Exception as e:
            pass

        print(f"Processing {title}.grobid.tei.xml")
        doc.at[i, "Text"] = remove_xml_parts(f"doct/{title}/doc.grobid.tei.xml")
        with open(f"output/{title}.txt", "w", encoding="utf-8") as file:
            file.write(doc.at[i, "Text"])
    else:
        print(f"Reading and copying {title}.txt")
        with open(f"output/{title}.txt", "r", encoding="utf-8") as file:
            doc.at[i, "Text"] = file.read()

def download_doctorates(doc, i):
    title = re.sub(r'[<>:"/\\|?*]', '_', doc["Title"][i])
    title = re.sub(r'\s+', ' ', title).strip().replace(' ', '_')[:255]
    timeout_counter = 5
    while timeout_counter > 0:
        timeout_counter -= 1
        try:
            if not os.path.exists(f"doct/{title}/doc.grobid.tei.xml") and not is_pdf_valid(f"doct/{title}/doc.pdf"):
                try:
                    os.makedirs(f"doct/{title}")
                except FileExistsError:
                    pass

                try:
                    print(f"{title}.pdf download")
                    URL.urlretrieve(doc["File"][i], filename=f"doct/{title}/doc.pdf")
                except Exception as e:
                    print(f"url error: {e}")
        except Exception:
            pass

def process_one(file_path):
    df_doc = pd.read_csv(file_path)
    display.display(df_doc)
    doctorate_count = len(df_doc)


    with ThreadPoolExecutor() as executor:
        executor.map(lambda i: download_doctorates(df_doc, i), range(doctorate_count))

    with ThreadPoolExecutor() as executor:
        executor.map(lambda i: doctorate_execute(df_doc, i), range(doctorate_count))

    df_doc = df_doc.dropna(subset=["Text"])
    output_file = file_path.replace("doctorates_", "doctorates_with_text_")
    df_doc.to_csv(output_file, sep='|', index=False)


if __name__ == "__main__":
    socket.setdefaulttimeout(60)
    #spacy.require_gpu()
    #download("pl_core_news_sm")
    #download("en_core_web_lg")
    try:
        nlp = spacy.load("./spacy")
    except Exception:
        nlp = spacy.load("pl_core_news_sm")
        nlp.add_pipe("sentencizer")
        nlp.add_pipe("language_detector", last=True)
        nlp = training(nlp)
        nlp.to_disk("./spacy")

    csv_files = glob.glob("./doctorates_*.csv")
    for file in csv_files:
        process_one(file)
