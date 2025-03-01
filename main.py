from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
import time

# Set up Selenium WebDriver
chrome_options = Options()
# chrome_options.add_argument("--headless")  # Run in headless mode (optional)
service = Service("/usr/lib/chromium/chromedriver-linux64/chromedriver")  # Replace with the correct path to chromedriver
driver = webdriver.Chrome(service=service, options=chrome_options)

# URL of the target page
url = "https://ppm.edu.pl/globalResultList.seam?r=phd&tab=PHD&lang=pl&qp=openAccess%253Dtrue%2526author%253Aauthor%253D%2526hasFileAttached%253Dtrue%2526date1%253D%2526date2%253D&pn=5&p=top&ps=100"
driver.get(url)
time.sleep(5)  # Allow the page to load

# Extract doctorate details
doctorates = []
entries = driver.find_elements(By.CSS_SELECTOR, ".entities-table-row")

for entry in entries:
    try:
        title_elem = entry.find_element(By.CSS_SELECTOR, ".entity-row-title a")
        title = title_elem.text.strip()
        doctorate_url = title_elem.get_attribute("href")

        # License information
        license_elem = entry.find_elements(By.CSS_SELECTOR, ".fileInfoTooltip .ui-tooltip-text span")
        license_text = license_elem[0].text.strip() if license_elem else "Unknown"

        # File links
        file_links = []
        file_elems = entry.find_elements(By.CSS_SELECTOR, ".fileDownloadLink")
        for file_elem in file_elems:
            file_links.append(file_elem.get_attribute("href"))

        doctorates.append({
            "Title": title,
            "URL": doctorate_url,
            "License": license_text,
            "Files": file_links
        })

    except Exception as e:
        print(f"Error extracting entry: {e}")

# Close WebDriver
driver.quit()

# Output results
for doc in doctorates:
    print(doc)
