import logging
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
import time
from selenium.common.exceptions import StaleElementReferenceException, NoSuchElementException
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
import re
import csv
import os
ALL_LICENSES = ["CC BY-SA", "CC BY-NC", "CC BY-NC-SA", "CC BY", "CC BY-ND", "CC BY-NC-ND"]


def navigate_to_page(page_number):
    try:
        # Click the button to activate input
        button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "page-inplace-input-inactive"))
        )
        button.click()

        # Wait for the input field to appear
        input_field = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CLASS_NAME, "entitiesDataListPageInput"))
        )

        # Clear the existing value
        input_field.send_keys(Keys.DELETE)

        # Enter the new page number
        input_field.send_keys(str(page_number))
        time.sleep(0.5)

        # Press Enter
        input_field.send_keys(Keys.ENTER)

        # Wait 15 seconds for the page to load
        time.sleep(20)

    except Exception as e:
        print(f"Error during navigation: {e}")

def normalize_license(text):
    # Replace -, _, or whitespace with a single space
    text = re.sub(r"[-_\s]+", " ", text.strip())
    # Remove extra spaces and normalize to match list
    return text.upper()


def find_license(license_text):
    # Build regex to find something starting with CC
    pattern = r"(CC[-_\s]*BY([-_\s]*(NC|ND))?([-_\s]*SA)?([-_\s]*ND)?)"
    match = re.search(pattern, license_text, re.IGNORECASE)
    if not match:
        return None

    found = match.group(0)
    normalized = normalize_license(found)

    # Try to match normalized against ALL_LICENSES
    for lic in ALL_LICENSES:
        if normalize_license(lic) == normalized:
            return lic  # Return the canonical form

    return None  # No match found


def is_license_allowed(license_text):
    license_found = find_license(license_text)
    if not license_found:
        return False, None

    allowed = license_found in ALLOWED_LICENSES
    return allowed, license_found


def save_doctorates_to_csv(doctorates, fieldnames, file_path):
    # Check if file exists and is not empty
    file_exists = os.path.isfile(file_path)
    file_empty = not file_exists or os.path.getsize(file_path) == 0

    with open(file_path, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        if file_empty:
            writer.writeheader()
        for doc in doctorates:
            writer.writerow({key: doc.get(key, "") for key in fieldnames})

    print(f"Metadata saved")


def scrape_page(url, doctorates, empty_doctorates, ALLOWED_LICENSES, START_PAGE, END_PAGE):
    """Scrape all doctorate entries from a given results page, including pagination."""
    logging.info(f"Scraping results from: {url}")
    page_id = START_PAGE - 1
    id = page_id*100
    driver.get(url)
    navigate_to_page(START_PAGE)

    processed_entries = set()  # Keep track of already processed URLs

    while True:
        try:
            page_doctorates = []
            page_id += 1
            if page_id >= END_PAGE:
                logging.info(f"Reached last page specified in config, page: {page_id}")
                return empty_doctorates

            entries = get_entries()
            number_of_entries = len(entries)
            number_of_processed = 0
            logging.info(f"Found {len(entries)} doctorates on this page.")

            for i in range(len(entries)):
                try:
                    id += 1

                    title, doctorate_url = get_title_and_url(entries[i])
                    file_link, license = get_file_link(entries[i], ALLOWED_LICENSES)

                    if not file_link:
                        file_link, license = attempt_to_get_file_from_overlay(entries[i], ALLOWED_LICENSES)

                    if doctorate_url in processed_entries:
                        logging.info(f"Skipping already processed entry: {title}")
                        number_of_processed += 1
                        continue  # Avoid duplicates

                    if file_link and license:
                        page_doctorates.append({
                            "Title": title,
                            "URL": doctorate_url,
                            "License": license,
                            "ID": id,
                            "File": file_link
                        })
                        doctorates.append(page_doctorates[-1])
                        processed_entries.add(doctorate_url)
                        logging.info(f"Added doctorate {len(page_doctorates)-1} from entry {id}: {title} - {file_link}")
                    elif license and not file_link:
                        empty_doctorates += 1
                        logging.info(f"Wrong file link for file: {title}")
                    elif file_link and not license:
                        empty_doctorates += 1
                        logging.info(f"Wrong license for: {title}")
                    else:
                        empty_doctorates += 1
                        logging.info(f"No file link and wrong license for: {title}")

                    number_of_processed += 1

                except (StaleElementReferenceException, NoSuchElementException) as e:
                    logging.warning(f"Stale element encountered for entry {i}. Skipping this entry.")
                    break

            if number_of_processed < number_of_entries:
                # retry stale
                driver.refresh()
                time.sleep(2)  # Wait for the page to load
                continue

        except Exception as e:
            logging.error(f"Error scraping page: {e}")
            break  # Break out of the loop if there's an error

        # Pagination handling
        try:
            # Check for "Next" button to navigate to the next page
            next_button = driver.find_element(By.CSS_SELECTOR, ".ui-paginator-next")
            if "ui-state-disabled" in next_button.get_attribute("class"):
                logging.info("Reached the last page. No more pages to scrape.")
                return empty_doctorates  # No more pages, exit the loop

            logging.info(f"Saving page {page_id}")
            save_doctorates_to_csv(page_doctorates, ["ID", "Title", "URL", "License"], "doctorates_metadata.csv")
            save_doctorates_to_csv(page_doctorates, ["Title", "URL", "License", "ID", "File"], "file_links.csv")
            logging.info(f"Saved page {page_id}")

            logging.info("Clicking Next page...")
            next_button.click()
            time.sleep(10)  # Wait for next page to load

        except Exception as e:
            logging.info(f"Reached the last page.")
            break

    return empty_doctorates


def get_entries():
    """Retrieve all entries from the current page."""
    return driver.find_elements(By.CSS_SELECTOR, ".entities-table-row")


def get_title_and_url(entry):
    """Extract title and URL from a given entry."""
    title_elem = entry.find_element(By.CSS_SELECTOR, ".entity-row-title a")
    title = title_elem.text.strip()
    doctorate_url = title_elem.get_attribute("href")
    return title, doctorate_url


def get_file_link(entry, ALLOWED_LICENSES):
    """Try to get the file download link from the entry."""
    try:
        file_element = entry.find_element(By.CSS_SELECTOR, ".fileDownloadLink")
        license = get_license(file_element, ALLOWED_LICENSES)
        return file_element.get_attribute("href"), license
    except:
        return None, None  # No file available


def get_license(file_element, ALLOWED_LICENSES):
    """Try to get the file download link from the entry if license is acceptable."""
    try:
        # Hover over the file element to trigger the tooltip
        ActionChains(driver).move_to_element(file_element).perform()

        # Wait for the tooltip to appear
        tooltips = driver.find_elements(By.CSS_SELECTOR, ".fileInfoTooltip")
        tooltips = list(filter(lambda element: element.text != '', tooltips))

        if tooltips[0] is None:
            logging.error(f"Failed to retrieve tooltip.")
            return None

        tooltip_text = tooltips[-1].text

        allowed, license_name = is_license_allowed(tooltip_text)
        if allowed:
            return license_name
        else:
            return None

    except Exception as e:
        # Handle no file, no tooltip, timeout, etc.
        return None



def attempt_to_get_file_from_overlay(entry, ALLOWED_LICENSES):
    """Attempt to retrieve file link by clicking the copy icon inside a specific entry."""
    button_selector = "i.fa.fa-copy"
    overlay_selector = "div.multiFilesDownloadOverlayPanel.ui-overlay-visible"
    file_link_selector = "div.filesDownloadPanel a.fileDownloadLink"

    try:
        # Find the copy icon inside the given entry
        icon_elem = entry.find_element(By.CSS_SELECTOR, button_selector)

        time.sleep(1)
        # Click on the icon to open the overlay
        action = webdriver.ActionChains(driver)
        action.move_to_element(icon_elem).pause(0.5).click().perform()

        # Wait for the overlay panel to appear
        WebDriverWait(driver, 20).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, overlay_selector))
        )

        time.sleep(1)  # Ensure files are loaded

        # Get all file links inside the overlay panel
        file_elems = entry.find_elements(By.CSS_SELECTOR, file_link_selector)
        if file_elems:
            file_element = file_elems[0]
            license = get_license(file_element, ALLOWED_LICENSES)
            return file_element.get_attribute("href"), license  # Select the first file
        else:
            logging.warning("No file links found in overlay panel.")
            return None, None

    except Exception as e:
        logging.warning(f"Failed to retrieve file from overlay.")
        return None, None


if __name__ == "__main__":
    # Logging setup
    logging.basicConfig(
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt='%Y-%m-%d %H:%M:%S',
        level=logging.INFO,
        handlers = [
            logging.FileHandler("debug.log", 'a', 'utf-8'),
            logging.StreamHandler()
        ]
    )

    with open('config.json', 'r') as f:
        config = json.load(f)
        URL = config["URL"]
        ALLOWED_LICENSES = config["ALLOWED_LICENSES"]
        HEADLESS_BROWSER = config["HEADLESS_BROWSER"]
        START_PAGE = config["START_PAGE"]
        END_PAGE = config["END_PAGE"]

    # Configure Selenium options
    chrome_options = Options()
    if HEADLESS_BROWSER == 1:
        chrome_options.add_argument("--headless")  # Run headless mode for speed
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    # Initialize WebDriver
    driver = webdriver.Chrome(options=chrome_options)

    doctorates = []
    empty_doctorates = 0

    empty_doctorates = scrape_page(URL, doctorates, empty_doctorates, ALLOWED_LICENSES, START_PAGE, END_PAGE)

    # Close WebDriver
    driver.quit()

    # Output results
    logging.info(f"Scraping complete. Total doctorates collected: {len(doctorates)}; Doctorates without pdf attached or wrong license: {empty_doctorates}")