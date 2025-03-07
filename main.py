import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time
from selenium.common.exceptions import StaleElementReferenceException, NoSuchElementException

# Logging setup
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# Path to ChromeDriver
CHROMEDRIVER_PATH = "/usr/lib/chromium/chromedriver-linux64/chromedriver"

# List of pre-filtered URLs (already contains only allowed licenses)
FILTERED_URLS = [
    "https://ppm.edu.pl/resultList.seam?aq=.%3Aee6549ffc7dd4be0bd1ee75316dafe55&r=phd&ps=100&t=snippet&showRel=false&lang=pl&pn=1&cid=1864505",
    "https://ppm.edu.pl/resultList.seam?aq=.%3Aca2a18e81f674e01a71e1adb8f31a7e8&r=phd&ps=100&t=snippet&showRel=false&lang=pl&pn=1&cid=1864532",
    "https://ppm.edu.pl/resultList.seam?aq=.%3Ab10aa19e712b47a39463f17f3401e58a&r=phd&ps=100&t=snippet&showRel=false&lang=pl&pn=1&cid=1864536"
]

# Configure Selenium options
chrome_options = Options()
chrome_options.add_argument("--headless")  # Run headless mode for speed
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

# Initialize WebDriver
service = Service(CHROMEDRIVER_PATH)
driver = webdriver.Chrome(service=service, options=chrome_options)

doctorates = []

def scrape_page(url):
    """Scrape all doctorate entries from a given results page, including pagination."""
    logging.info(f"Scraping results from: {url}")
    driver.get(url)
    time.sleep(5)  # Wait for the page to load

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
                            "File": file_link
                        })
                        logging.info(f"✅ Added: {title} - {file_link}")
                    else:
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

# Scrape each filtered URL
for url in FILTERED_URLS:
    scrape_page(url)

# Close WebDriver
driver.quit()

# Output results
logging.info(f"Scraping complete. Total doctorates collected: {len(doctorates)}")
for doc in doctorates:
    logging.info(doc)
