from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Set up the service object with the path to chromedriver
service = Service("./chromedriver")

# Initialize the Chrome driver with the service
driver = webdriver.Chrome(service=service)

# Open DuckDuckGo
driver.get("https://golfnow.co.uk/tee-times/facility/17547/search")

try:
    # Wait up to 10 seconds for the element with class name "search__input" to be present
    element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "time-meridian"))
    )
    # Print the text value of the found element
    print("First Tee Time:", element.text)
except:
    print("Element not found")
finally:
    input("Press Enter to close the browser...")
    driver.quit()
