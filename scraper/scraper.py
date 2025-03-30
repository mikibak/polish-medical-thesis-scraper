import logging
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time
from selenium.common.exceptions import StaleElementReferenceException, NoSuchElementException
import csv
import pandas as pd
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json


def save_doctorates_to_csv(doctorates):
    # Get the field names from the first dictionary
    fieldnames = ["ID", "Title", "URL", "License"]
    
    with open("scraper/doctorates_metadata.csv", mode='w', newline='', encoding='utf-8') as file:
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
            entries = get_entries()
            logging.info(f"Found {len(entries)} doctorates on this page.")

            for i in range(len(entries)):
                try:
                    # Re-locate elements to avoid stale element error
                    entries = get_entries()
                    title, doctorate_url = get_title_and_url(entries[i])
                    file_link = get_file_link(entries[i])

                    if not file_link:
                        file_link = attempt_to_get_file_from_overlay()

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

        # Pagination handling
        try:
            # Check for "Next" button to navigate to the next page
            next_button = driver.find_element(By.CSS_SELECTOR, ".ui-paginator-next")
            if "ui-state-disabled" in next_button.get_attribute("class"):
                logging.info("Reached the last page. No more pages to scrape.")
                return empty_doctorates, id  # No more pages, exit the loop

            logging.info("Clicking Next page...")
            next_button.click()
            time.sleep(5)  # Wait for next page to load

        except Exception as e:
            logging.error(f"Error navigating to the next page. Reached the last page.")
            break

    return empty_doctorates, id


def get_entries():
    """Retrieve all entries from the current page."""
    return driver.find_elements(By.CSS_SELECTOR, ".entities-table-row")


def get_title_and_url(entry):
    """Extract title and URL from a given entry."""
    title_elem = entry.find_element(By.CSS_SELECTOR, ".entity-row-title a")
    title = title_elem.text.strip()
    doctorate_url = title_elem.get_attribute("href")
    return title, doctorate_url


def get_file_link(entry):
    """Try to get the file download link from the entry."""
    try:
        file_elem = entry.find_element(By.CSS_SELECTOR, ".fileDownloadLink")
        return file_elem.get_attribute("href")
    except:
        return None  # No file available


def attempt_to_get_file_from_overlay():
    """Attempt to retrieve file link by clicking the copy icon and opening the overlay."""
    button_selector = "i.fa.fa-copy"
    for attempt in range(3):  # Retry mechanism
        try:
            icon_elem = WebDriverWait(driver, 4).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, button_selector))
            )
            ActionChains(driver).move_to_element(icon_elem).click().perform()
            ActionChains(driver).move_to_element(icon_elem).click().perform()

            # Wait for the overlay panel to appear
            WebDriverWait(driver, 5).until(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, ".multiFilesDownloadOverlayPanel.ui-overlay-visible")
                )
            )
            break  # Exit loop if click succeeds
        except Exception:
            logging.warning(f"Retry {attempt + 1}/3: Failed to click copy icon, retrying...")
            continue

    time.sleep(2)  # Ensure files are loaded

    # Get all file links inside the overlay panel
    file_elems = driver.find_elements(By.CSS_SELECTOR, ".multiFilesDownloadOverlayPanel .fileDownloadLink")
    if file_elems:
        return file_elems[0].get_attribute("href")  # Select the first file
    else:
        logging.warning(f"⚠️ No file links found in overlay panel.")
        return None


if __name__ == "__main__":
    # Logging setup
    logging.basicConfig(
        format="%(asctime)s - %(levelname)s - %(message)s",
        level=logging.INFO
    )

    # List of pre-filtered URLs (already contains only allowed licenses)
    with open('scraper/config.json', 'r') as f:
        config = json.load(f)
        FILTERED_URLS = config["FILTERED_URLS"]

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
        id += added_id

    # Close WebDriver
    driver.quit()

    # Output results
    logging.info(f"Scraping complete. Total doctorates collected: {len(doctorates)}; Doctorates without pdf attached: {empty_doctorates}")

    save_doctorates_to_csv(doctorates)

    df_doc = pd.DataFrame(data=doctorates)
    df_doc.to_csv("scraper/file_links.csv", index=False)
