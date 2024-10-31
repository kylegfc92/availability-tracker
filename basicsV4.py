import csv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Function to read facility names and IDs from a CSV file
def read_facilities_from_csv(file_path):
    facilities = []
    with open(file_path, mode='r', encoding='utf-8-sig') as csv_file:  # Use utf-8-sig to handle BOM
        csv_reader = csv.DictReader(csv_file)
        for row in csv_reader:
            facility_name = row['facility_name'].strip()  # Strip whitespace from facility name
            facility_id = row['facility_id'].strip()      # Strip whitespace from facility ID
            facilities.append((facility_name, facility_id))
    return facilities

# Read facilities from the CSV file
facilities = read_facilities_from_csv("Test.csv")

# Set up the service object with the path to chromedriver
service = Service("./chromedriver")

# Initialize the Chrome driver with the service
driver = webdriver.Chrome(service=service)

# Loop through each facility
for facility_name, facility_id in facilities:
    # Construct the URL using the current facility ID
    url = f"https://golfnow.co.uk/tee-times/facility/{facility_id}/search"
    print(f"\nSearching for {facility_name}: {facility_id}")

    # Open the URL
    driver.get(url)

    try:
        # Wait up to 10 seconds for elements with the class name "time-meridian" to be present
        elements = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "time-meridian"))
        )

        # Check if elements were found
        if elements:
            first_element_text = elements[0].text  # Text of the first instance
            last_element_text = elements[-1].text  # Text of the last instance

            print(f"First Tee Time for {facility_name}:", first_element_text)
            print(f"Last Tee Time for {facility_name}:", last_element_text)
        else:
            print(f"No elements found with the class name 'time-meridian' for {facility_name}")
    except:
        print(f"No elements found or an error occurred for {facility_name}: {facility_id}")

# Close the browser after checking all URLs
driver.quit()
