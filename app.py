import csv
import os
import logging
from flask import Flask, request, render_template, redirect, url_for, flash
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# Initialize Flask app and logging
app = Flask(__name__)
app.secret_key = "secret_key"
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Set up logging
logging.basicConfig(filename="app.log", level=logging.DEBUG, format="%(asctime)s %(levelname)s:%(message)s")
logging.debug("Flask app initialized.")

# Function to read facility names and IDs from a CSV file
def read_facilities_from_csv(file_path):
    logging.debug(f"Reading CSV file from {file_path}")
    facilities = []
    try:
        with open(file_path, mode='r', encoding='utf-8-sig') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            for row in csv_reader:
                facility_name = row['facility_name'].strip()
                facility_id = row['facility_id'].strip()
                facilities.append((facility_name, facility_id))
        logging.debug(f"Facilities found: {facilities}")
    except Exception as e:
        logging.error(f"Error reading CSV file: {e}")
    return facilities

# Route to render the upload form and display results
@app.route("/", methods=["GET", "POST"])
def upload_file():
    logging.debug("Upload file route called.")
    if request.method == "POST":
        if "file" not in request.files:
            flash("No file uploaded.")
            logging.warning("No file part in request.")
            return redirect(request.url)

        file = request.files["file"]
        if file.filename == "":
            flash("No selected file.")
            logging.warning("No file selected.")
            return redirect(request.url)

        if file:
            file_path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
            file.save(file_path)
            logging.debug(f"File saved to {file_path}")

            facilities = read_facilities_from_csv(file_path)

            # Initialize the Selenium WebDriver with headless options
            options = Options()
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--disable-software-rasterizer")

            service = Service("/usr/local/bin/chromedriver")
            driver = webdriver.Chrome(service=service, options=options)
            logging.debug("WebDriver initialized in headless mode.")

            results = []
            for facility_name, facility_id in facilities:
                url = f"https://golfnow.co.uk/tee-times/facility/{facility_id}/search"
                logging.debug(f"Accessing URL: {url} for facility {facility_name} with ID {facility_id}")
                
                try:
                    driver.get(url)
                    elements = WebDriverWait(driver, 10).until(
                        EC.presence_of_all_elements_located((By.CLASS_NAME, "time-meridian"))
                    )

                    if elements:
                        first_element_text = elements[0].text
                        last_element_text = elements[-1].text
                        results.append({
                            "facility_name": facility_name,
                            "facility_id": facility_id,
                            "first_tee_time": first_element_text,
                            "last_tee_time": last_element_text
                        })
                        logging.debug(f"Times found for {facility_name}: First - {first_element_text}, Last - {last_element_text}")
                    else:
                        results.append({
                            "facility_name": facility_name,
                            "facility_id": facility_id,
                            "first_tee_time": "No tee time found",
                            "last_tee_time": "No tee time found"
                        })
                        logging.warning(f"No times found for {facility_name}")

                except TimeoutException:
                    logging.error(f"TimeoutException: No elements found for {facility_name} (ID: {facility_id})")
                    results.append({
                        "facility_name": facility_name,
                        "facility_id": facility_id,
                        "first_tee_time": "No tee time found",
                        "last_tee_time": "No tee time found"
                    })
                except Exception as e:
                    logging.error(f"Error occurred for {facility_name} (ID: {facility_id}): {str(e)}")
                    results.append({
                        "facility_name": facility_name,
                        "facility_id": facility_id,
                        "error": f"Error occurred: {str(e)}"
                    })

            driver.quit()
            logging.debug("WebDriver closed.")

            return render_template("results.html", results=results)
    
    return render_template("upload.html")

# Run the Flask app
if __name__ == "__main__":
    app.run(debug=True)
