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
- Grobid (full or reduced version) container running (https://grobid.readthedocs.io/en/latest/Grobid-docker/)
- Grobid client
  ```sh
  pip install grobid-client
  ```
- Required Python dependencies

## Usage
### 1. Select Licenses
- Go to [ppm.edu.pl](https://ppm.edu.pl/) and select an entry with the desired license
- Click the license to search for all files with the same license
- Add the link to the config file (`config.json`)
- Repeat for all license types that need to be scraped.

### 2. Run the Scraper
```sh
python scraper/scraper.py
```
This will collect metadata, including titles, URLs, and PDF links.

### 3. Process PDFs with Grobid
```sh
python pdf_to_text/download_and_process_pdfs.py
```
This will extract text from the downloaded PDFs and save them as `.txt` files.

## Contributors
- **mikibak**
- **kubson0226**
- **kubix23**
- **cariotic**

## License
This project is licensed under the MIT license.
