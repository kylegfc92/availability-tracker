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

app = Flask(__name__)
app.secret_key = "secret_key"
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Setup logging
logging.basicConfig(
    filename="app.log",
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s:%(message)s"
)
logging.debug("Flask app initialized.")

# Function to read facility names and IDs from a CSV file
def read_facilities_from_csv(file_path):
    facilities = []
    logging.debug(f"Reading facilities from {file_path}")
    try:
        with open(file_path, mode='r', encoding='utf-8-sig') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            for row in csv_reader:
                facility_name = row['facility_name'].strip()
                facility_id = row['facility_id'].strip()
                facilities.append((facility_name, facility_id))
        logging.debug("Successfully read facilities from CSV.")
    except Exception as e:
        logging.error(f"Error reading CSV file: {e}")
    return facilities

# Route to render the upload form and display results
@app.route("/", methods=["GET", "POST"])
def upload_file():
    logging.debug("Received request on / route.")
    if request.method == "POST":
        logging.debug("Processing POST request.")
        
        # Check if a file is provided
        if "file" not in request.files:
            flash("No file uploaded.")
            logging.warning("No file part in request.")
            return redirect(request.url)

        file = request.files["file"]
        if file.filename == "":
            flash("No selected file.")
            logging.warning("No file selected for upload.")
            return redirect(request.url)

        if file:
            file_path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
            file.save(file_path)
            logging.debug(f"File saved to {file_path}")
            facilities = read_facilities_from_csv(file_path)

            # Configure headless Chrome options
            chrome_options = Options()
            chrome_options.add_argument("--headless")  
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-software-rasterizer")

            # Initialize the Selenium WebDriver with headless options
            service = Service("./chromedriver")  # Adjust path if necessary
            driver = webdriver.Chrome(service=service, options=chrome_options)

            results = []
            for facility_name, facility_id in facilities:
                logging.debug(f"Processing facility: {facility_name} with ID: {facility_id}")
                url = f"https://golfnow.co.uk/tee-times/facility/{facility_id}/search"
                
                try:
                    driver.get(url)
                    elements = WebDriverWait(driver, 2).until(
                        EC.presence_of_all_elements_located((By.CLASS_NAME, "time-meridian"))
                    )
                    logging.debug(f"Elements found for {facility_name} with ID: {facility_id}")

                    if elements:
                        first_element_text = elements[0].text
                        last_element_text = elements[-1].text
                        results.append({
                            "facility_name": facility_name,
                            "facility_id": facility_id,
                            "first_tee_time": first_element_text,
                            "last_tee_time": last_element_text
                        })
                    else:
                        results.append({
                            "facility_name": facility_name,
                            "facility_id": facility_id,
                            "first_tee_time": "No tee time found",
                            "last_tee_time": "No tee time found"
                        })

                except TimeoutException:
                    logging.error(f"Timeout while processing {facility_name} with ID: {facility_id}")
                    results.append({
                        "facility_name": facility_name,
                        "facility_id": facility_id,
                        "first_tee_time": "No tee time found",
                        "last_tee_time": "No tee time found"
                    })

            driver.quit()
            logging.debug("WebDriver quit successfully.")
            return render_template("results.html", results=results)
    
    return render_template("upload.html")

# Run the Flask app
if __name__ == "__main__":
    logging.debug("Starting Flask app.")
    app.run(debug=True)
