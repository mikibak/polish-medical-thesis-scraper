from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time

# Set up Selenium WebDriver
chrome_options = Options()
# chrome_options.add_argument("--headless")  # Run in headless mode (optional)
service = Service("/usr/lib/chromium/chromedriver-linux64/chromedriver")  # Use correct path
driver = webdriver.Chrome(service=service, options=chrome_options)

# URL of the first page
url = "https://ppm.edu.pl/globalResultList.seam?r=phd&tab=PHD&lang=pl&qp=openAccess%253Dtrue%2526author%253Aauthor%253D%2526hasFileAttached%253Dtrue%2526date1%253D%2526date2%253D&pn=1&p=top&ps=100"
driver.get(url)
time.sleep(5)  # Allow the page to load

doctorates = []
scraped_pages = 0
max_scraped_pages = 3


def scrape_page():
    """Extract doctorate details from the current page"""
    entries = driver.find_elements(By.CSS_SELECTOR, ".entities-table-row")

    for entry in entries:
        try:
            # Get title and URL
            title_elem = entry.find_element(By.CSS_SELECTOR, ".entity-row-title a")
            title = title_elem.text.strip()
            doctorate_url = title_elem.get_attribute("href")

            license_text, file_links = scrape_doctorate(doctorate_url)

            # Store data
            doctorates.append({
                "Title": title,
                "URL": doctorate_url,
                "License": license_text,
                "Files": file_links
            })

            # Close the tab and return to results page
            driver.close()
            driver.switch_to.window(driver.window_handles[0])

        except Exception as e:
            print(f"Error extracting entry: {e}")


def scrape_doctorate(doctorate_url):
    # Open the doctorate page
    driver.execute_script("window.open(arguments[0]);", doctorate_url)
    driver.switch_to.window(driver.window_handles[1])  # Switch to new tab
    time.sleep(2)  # Wait for page to load

    license_text = scrape_license()
    file_links = scrape_file_links()

    return license_text, file_links


def scrape_file_links():
    file_links = []
    file_elems = driver.find_elements(By.CSS_SELECTOR, ".fileDownloadLink")
    for file_elem in file_elems:
        file_links.append(file_elem.get_attribute("href"))

    return file_links


def scrape_license():
    try:
        license_elem = driver.find_element(By.CSS_SELECTOR, "form a span.inline-element")
        return license_elem.text.strip()
    except:
        return "Unknown"


while True:
    scrape_page()  # Scrape the current page
    scraped_pages += 1

    if scraped_pages >= max_scraped_pages:
        print('Max scraped pages number reached')
        break

    try:
        # Find the "Next" button and check if it's enabled
        next_button = driver.find_element(By.CSS_SELECTOR, ".ui-paginator-next")
        if "ui-state-disabled" in next_button.get_attribute("class"):
            print("Reached the last page.")
            break  # Exit loop when the last page is reached

        next_button.click()  # Click to go to the next page
        time.sleep(10)  # Wait for the page to load
    except:
        print("No more pages found or error clicking next button.")
        break  # Exit loop when no "Next" button is found

# Close WebDriver
driver.quit()

# Output results
for doc in doctorates:
    print(doc)
