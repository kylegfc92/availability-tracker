import csv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Function to read facility IDs from a CSV file
def read_facility_ids_from_csv(file_path):
    facility_ids = []
    with open(file_path, mode='r') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for row in csv_reader:
            facility_ids.append(row['facility_id'])
    return facility_ids

# Read facility IDs from the CSV file
facility_ids = read_facility_ids_from_csv("Test.csv")

# Set up the service object with the path to chromedriver
service = Service("./chromedriver")

# Initialize the Chrome driver with the service
driver = webdriver.Chrome(service=service)

# Loop through each facility ID
for facility_id in facility_ids:
    # Construct the URL using the current facility ID
    url = f"https://golfnow.co.uk/tee-times/facility/{facility_id}/search"
    print(f"\nSearching for facility ID: {facility_id}")
    
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

            print("First Tee Time:", first_element_text)
            print("Last Tee Time:", last_element_text)
        else:
            print("No elements found with the class name 'time-meridian'")
    except:
        print("No Tee Times found or an error occurred for facility ID:", facility_id)

# Close the browser after checking all URLs
driver.quit()
