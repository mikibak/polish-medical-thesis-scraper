import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import concurrent.futures
import time

# Logging setup
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# Path to ChromeDriver
CHROMEDRIVER_PATH = "/usr/lib/chromium/chromedriver-linux64/chromedriver"

# Base URL
BASE_URL = "https://ppm.edu.pl/globalResultList.seam?r=phd&tab=PHD&lang=pl&qp=openAccess%253Dtrue%2526author%253Aauthor%253D%2526hasFileAttached%253Dtrue%2526date1%253D%2526date2%253D&pn=1&p=top&ps=100"

# Configure Selenium options
chrome_options = Options()
chrome_options.add_argument("--headless")  # Run headless mode
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

# Main WebDriver for pagination
service = Service(CHROMEDRIVER_PATH)
driver = webdriver.Chrome(service=service, options=chrome_options)
driver.get(BASE_URL)
time.sleep(10)  # Allow page to load (increased to 10s)

doctorates = []
scraped_pages = 0
max_scraped_pages = 3
MAX_WORKERS = 20  # Adaptive concurrency

logging.info("Scraper started. Navigating to the first results page.")


def scrape_doctorate(doctorate_url):
    """Scrape license and file links from an individual doctorate page."""
    try:
        logging.info(f"Opening doctorate page: {doctorate_url}")
        local_driver = webdriver.Chrome(service=Service(CHROMEDRIVER_PATH), options=chrome_options)
        local_driver.get(doctorate_url)
        time.sleep(3)  # Allow the page to load

        # Extract license
        try:
            license_elem = local_driver.find_element(By.CSS_SELECTOR, "form a span.inline-element")
            license_text = license_elem.text.strip()
        except:
            license_text = "Unknown"

        # Extract file links
        file_links = [elem.get_attribute("href") for elem in local_driver.find_elements(By.CSS_SELECTOR, ".fileDownloadLink")]

        local_driver.quit()
        logging.info(f"Scraped doctorate: {doctorate_url} | License: {license_text} | Files: {len(file_links)}")
        return license_text, file_links

    except Exception as e:
        logging.error(f"Error scraping {doctorate_url}: {e}")
        return "Unknown", []


def scrape_page():
    """Extract doctorate details from the current search results page."""
    logging.info("Scraping current search results page...")

    entries = driver.find_elements(By.CSS_SELECTOR, ".entities-table-row")
    logging.info(f"Found {len(entries)} doctorates on this page.")

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_entry = {}

        for entry in entries:
            try:
                title_elem = entry.find_element(By.CSS_SELECTOR, ".entity-row-title a")
                title = title_elem.text.strip()
                doctorate_url = title_elem.get_attribute("href")

                # Process each doctorate concurrently
                future = executor.submit(scrape_doctorate, doctorate_url)
                future_to_entry[future] = (title, doctorate_url)

            except Exception as e:
                logging.error(f"Error extracting entry: {e}")

        for future in concurrent.futures.as_completed(future_to_entry):
            title, doctorate_url = future_to_entry[future]
            license_text, file_links = future.result()

            # Store data
            doctorates.append({
                "Title": title,
                "URL": doctorate_url,
                "License": license_text,
                "Files": file_links
            })
            logging.info(f"Doctorate processed: {title}")


while True:
    logging.info(f"Processing page {scraped_pages + 1}...")
    scrape_page()
    scraped_pages += 1

    if scraped_pages >= max_scraped_pages:
        logging.info("Max scraped pages number reached. Stopping.")
        break

    try:
        next_button = driver.find_element(By.CSS_SELECTOR, ".ui-paginator-next")
        if "ui-state-disabled" in next_button.get_attribute("class"):
            logging.info("Reached the last page. No more pages to scrape.")
            break

        logging.info("Clicking Next page...")
        next_button.click()
        time.sleep(10)  # Wait for next page to load

    except:
        logging.error("No more pages found or error clicking Next button.")
        break

# Close main WebDriver
driver.quit()

# Output results
logging.info(f"Scraping complete. Total doctorates collected: {len(doctorates)}")
for doc in doctorates:
    logging.info(doc)
