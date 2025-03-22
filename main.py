import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time
from selenium.common.exceptions import StaleElementReferenceException, NoSuchElementException
import csv
import pandas as pd

empty_doctorates = 0
id = 0


def save_doctorates_to_csv(doctorates):
    # Get the field names from the first dictionary
    fieldnames = ["Title", "URL", "License"]
    
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for doc in doctorates:
            writer.writerow({key: doc.get(key, "") for key in fieldnames})

    print(f"Metadata saved")


def scrape_page(license, url, doctorates, empty_doctorates, id):
    """Scrape all doctorate entries from a given results page, including pagination."""
    logging.info(f"Scraping results from: {url}")
    driver.get(url)
    time.sleep(2)  # Wait for the page to load

    while True:
        try:
            entries = driver.find_elements(By.CSS_SELECTOR, ".entities-table-row")
            logging.info(f"Found {len(entries)} doctorates on this page.")

            for i in range(len(entries)):
                try:
                    # Re-locate elements to avoid stale element error
                    entries = driver.find_elements(By.CSS_SELECTOR, ".entities-table-row")
                    title_elem = entries[i].find_element(By.CSS_SELECTOR, ".entity-row-title a")
                    title = title_elem.text.strip()
                    doctorate_url = title_elem.get_attribute("href")

                    # Get file download link
                    try:
                        file_elem = entries[i].find_element(By.CSS_SELECTOR, ".fileDownloadLink")
                        file_link = file_elem.get_attribute("href")
                    except:
                        file_link = None  # No file available

                    if file_link:
                        doctorates.append({
                            "Title": title,
                            "URL": doctorate_url,
                            "License": license,
                            "ID": id,
                            "File": file_link
                        })
                        id += 1
                        logging.info(f"✅ Added {id}: {title} - {file_link}")
                    else:
                        empty_doctorates += 1
                        logging.warning(f"⚠️ No file link found for: {title}")

                except (StaleElementReferenceException, NoSuchElementException) as e:
                    logging.warning(f"⚠️ Stale element encountered for entry {i}. Skipping this entry.")
                    continue  # Skip this entry if it becomes stale

        except Exception as e:
            logging.error(f"Error scraping page: {e}")
            break  # Break out of the loop if there's an error

        try:
            # Check for "Next" button to navigate to the next page
            next_button = driver.find_element(By.CSS_SELECTOR, ".ui-paginator-next")
            if "ui-state-disabled" in next_button.get_attribute("class"):
                logging.info("Reached the last page. No more pages to scrape.")
                break  # No more pages, exit the loop

            logging.info("Clicking Next page...")
            next_button.click()
            time.sleep(5)  # Wait for next page to load

        except Exception as e:
            logging.error(f"Error navigating to the next page: {e}")
            break  # If there's an error (no next page or click failed), stop the loop
        finally:
            return empty_doctorates, id

if __name__ == "__main__":
    # Logging setup
    logging.basicConfig(
        format="%(asctime)s - %(levelname)s - %(message)s",
        level=logging.INFO
    )

    # List of pre-filtered URLs (already contains only allowed licenses)
    FILTERED_URLS = [
        ["CC BY-NC", "https://ppm.edu.pl/resultList.seam?aq=.%3Aee6549ffc7dd4be0bd1ee75316dafe55&r=phd&ps=100&t=snippet&showRel=false&lang=pl&pn=1&cid=1864505"],
        ["CC BY-SA", "https://ppm.edu.pl/resultList.seam?aq=.%3Aca2a18e81f674e01a71e1adb8f31a7e8&r=phd&ps=100&t=snippet&showRel=false&lang=pl&pn=1&cid=1864532"],
        ["CC BY", "https://ppm.edu.pl/resultList.seam?aq=.%3Ab10aa19e712b47a39463f17f3401e58a&r=phd&ps=100&t=snippet&showRel=false&lang=pl&pn=1&cid=1864536"]
    ]

    # Configure Selenium options
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run headless mode for speed
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    # Initialize WebDriver
    driver = webdriver.Chrome(options=chrome_options)

    doctorates = []
    empty_doctorates = 0
    id = 0
    added_empty_doctorates = 0
    added_id = 0

    # Scrape each filtered URL
    for url in FILTERED_URLS:
        added_empty_doctorates, added_id = scrape_page(url[0], url[1], doctorates, empty_doctorates, id)
        empty_doctorates += added_empty_doctorates
        added_id += id

    # Close WebDriver
    driver.quit()

    # Output results
    logging.info(f"Scraping complete. Total doctorates collected: {len(doctorates)}; Doctorates without pdf attached: {empty_doctorates}")

    save_doctorates_to_csv(doctorates)

    df_doc = pd.DataFrame(data=doctorates)
    df_doc.to_csv("doctorates.csv", index=False)
