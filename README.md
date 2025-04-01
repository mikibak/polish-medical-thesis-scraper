# Polish Medical Thesis Scraper

## Overview
This project is a web scraper designed to collect medical data in Polish, which can be used to train large language models (LLMs) for medical applications. It scrapes metadata and PDFs from ppm.edu.pl, processes the PDFs using Grobid, and extracts text into `.txt` files.

## Features
- Scrapes titles, URLs, and PDF links from ppm.edu.pl.
- Processes PDFs using Grobid to extract text.
- Outputs text data for further analysis and model training.

## Installation
### Requirements
- Python 3.x
- Grobid (full or reduced version) container running (https://grobid.readthedocs.io/en/latest/Grobid-docker/). Map container port 8070 to the port selected in `config.json` (default is also 8070).
  ```sh
  docker run -p 8070:8070 grobid/grobid:0.8.1
  ```
- Grobid client
  ```sh
  pip install grobid-client-python
  ```
- Required Python dependencies

## Usage
### 1. Select Licenses
- Go to [ppm.edu.pl](https://ppm.edu.pl/) and select an entry with the desired license
- Click the license to search for all files with the same license
- Add the link to the config file (`scraper/config.json`)
- Repeat for all license types that need to be scraped.
- Default license types in `scraper/config.json` are CC BY-SA, CC BY-NC, CC BY.

### 2. Run the Scraper
```sh
python scraper/scraper.py
```
This will collect metadata, including titles, URLs, and PDF links.

### 3. Divide file links into batches
```sh
python 1_divide_scraped_csv_into_batches.py
```
This will divide doctorates.csv into smaller csv files that can be then processed on multiple machines (though the project is not ready to be deployed on a cluster as-is)

### 4. Process PDFs with Grobid
```sh
python pdf_to_text/2_download_and_process_pdf_files.py
```
This will extract text from the downloaded PDFs and save them to doctorates_with_text_*.csv

### 5. Place text from all batches into .txt files
```sh
python pdf_to_text/3_extract_csv_to_txt_files.py
```
This will save collected text into one .txt file per title, file names are IDs assigned to each paper in doctorates_metadata.csv.

## Contributors
- [**mikibak**](https://github.com/mikibak)
- [**kubson0226**](https://github.com/kubson0226)
- [**kubix23**](https://github.com/kubix23)
- [**cariotic**](https://github.com/cariotic)

## License
This project is licensed under the MIT license.
