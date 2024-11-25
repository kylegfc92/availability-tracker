import csv
import os
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from concurrent.futures import ThreadPoolExecutor, as_completed

# Constants
UPLOAD_FOLDER = "/home/ubuntu/uploads"  # Directory for static CSV
STATIC_CSV = os.path.join(UPLOAD_FOLDER, "static_facilities.csv")  # Static input CSV
OUTPUT_CSV = "/home/ubuntu/results.csv"  # Path for output results CSV
LOG_FILE = "/home/ubuntu/app.log"
EMAIL_CONFIG = {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "email": "kyle.gfc8@gmail.com",
    "password": "Bloomfield1992",
    "recipient": "kyle.young@nbcuni.com",
}

# Configure logging
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s [%(filename)s:%(lineno)d] %(message)s"
)

# Function to read facility names and IDs from a CSV file
def read_facilities_from_csv("intl_fac_top50.csv"):
    logging.debug(f"Reading CSV file from {file_path}")
    facilities = []
    try:
        with open(file_path, mode="r", encoding="utf-8-sig") as csv_file:
            csv_reader = csv.DictReader(csv_file)
            for row in csv_reader:
                facilities.append((row["facility_name"].strip(), row["facility_id"].strip()))
        logging.debug(f"Facilities parsed: {facilities}")
    except Exception as e:
        logging.error(f"Error reading CSV file: {e}")
    return facilities

# Function to write results to a CSV file
def write_results_to_csv(results, file_path):
    logging.debug(f"Writing results to CSV file: {file_path}")
    try:
        with open(file_path, mode="w", encoding="utf-8-sig", newline="") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)
        logging.debug(f"Results written successfully to {file_path}")
    except Exception as e:
        logging.error(f"Error writing results to CSV: {e}")

# Function to fetch facility data using Selenium
def fetch_facility_data(facility_name, facility_id):
    logging.debug(f"Processing facility: {facility_name} with ID: {facility_id}")
    result = {"facility_name": facility_name, "facility_id": facility_id}
    try:
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-software-rasterizer")

        service = Service("/usr/local/bin/chromedriver")
        driver = webdriver.Chrome(service=service, options=options)

        url = f"https://golfnow.co.uk/tee-times/facility/{facility_id}/search"
        logging.debug(f"Fetching URL: {url}")
        driver.get(url)

        try:
            elements = WebDriverWait(driver, 5).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, "time-meridian"))
            )
            if elements:
                result["first_tee_time"] = elements[0].text
                result["last_tee_time"] = elements[-1].text
                logging.debug(f"Times for {facility_name}: First - {result['first_tee_time']}, Last - {result['last_tee_time']}")
            else:
                result["first_tee_time"] = "No tee time found"
                result["last_tee_time"] = "No tee time found"
        except TimeoutException:
            result["first_tee_time"] = "No tee time found"
            result["last_tee_time"] = "No tee time found"
            logging.warning(f"Timeout for {facility_name}")
        driver.quit()
    except Exception as e:
        logging.error(f"Error for {facility_name} (ID: {facility_id}): {str(e)}")
        result["error"] = f"Error: {str(e)}"
    return result

# Function to send email with CSV attachment
def send_email_with_attachment(subject, body, attachment_path):
    try:
        logging.debug(f"Sending email to {EMAIL_CONFIG['recipient']}")
        msg = MIMEMultipart()
        msg["From"] = EMAIL_CONFIG["email"]
        msg["To"] = EMAIL_CONFIG["recipient"]
        msg["Subject"] = subject

        msg.attach(MIMEText(body, "plain"))

        # Attach CSV file
        with open(attachment_path, "rb") as attachment:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f"attachment; filename={os.path.basename(attachment_path)}")
        msg.attach(part)

        with smtplib.SMTP(EMAIL_CONFIG["smtp_server"], EMAIL_CONFIG["smtp_port"]) as server:
            server.starttls()
            server.login(EMAIL_CONFIG["email"], EMAIL_CONFIG["password"])
            server.sendmail(EMAIL_CONFIG["email"], EMAIL_CONFIG["recipient"], msg.as_string())
        logging.debug("Email sent successfully.")
    except Exception as e:
        logging.error(f"Error sending email: {e}")

# Main job function
def run_job():
    logging.debug("Starting scheduled job.")
    facilities = read_facilities_from_csv(STATIC_CSV)
    results = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(fetch_facility_data, name, fid) for name, fid in facilities]
        for future in as_completed(futures):
            results.append(future.result())

    write_results_to_csv(results, OUTPUT_CSV)
    send_email_with_attachment(
        subject="Daily Facility Report",
        body="Please find the attached results.",
        attachment_path=OUTPUT_CSV
    )
    logging.debug("Scheduled job completed.")

if __name__ == "__main__":
    run_job()
