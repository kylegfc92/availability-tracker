import csv
import os
from flask import Flask, request, render_template, redirect, url_for, flash
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

app = Flask(__name__)
app.secret_key = "secret_key"
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Function to read facility names and IDs from a CSV file
def read_facilities_from_csv(file_path):
    facilities = []
    with open(file_path, mode='r', encoding='utf-8-sig') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for row in csv_reader:
            facility_name = row['facility_name'].strip()
            facility_id = row['facility_id'].strip()
            facilities.append((facility_name, facility_id))
    return facilities

# Route to render the upload form and display results
@app.route("/", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        # Check if a file is provided
        if "file" not in request.files:
            flash("No file uploaded.")
            return redirect(request.url)

        file = request.files["file"]
        if file.filename == "":
            flash("No selected file.")
            return redirect(request.url)

        if file:
            file_path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
            file.save(file_path)
            facilities = read_facilities_from_csv(file_path)

                    # Initialize the Selenium WebDriver with headless options
        service = Service("/usr/local/bin/chromedriver")  # Adjust path if necessary
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        driver = webdriver.Chrome(service=service, options=options)

        results = []
        for facility_name, facility_id in facilities:
            url = f"https://golfnow.co.uk/tee-times/facility/{facility_id}/search"
            driver.get(url)

            try:
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
                else:
                    results.append({
                        "facility_name": facility_name,
                        "facility_id": facility_id,
                        "first_tee_time": "No tee time found",
                        "last_tee_time": "No tee time found"
                    })
            except Exception as e:
                results.append({
                    "facility_name": facility_name,
                    "facility_id": facility_id,
                    "error": f"Error occurred: {str(e)}"
                })

        driver.quit()

        return render_template("results.html", results=results)

    return render_template("upload.html")

# Run the Flask app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
