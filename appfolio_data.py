from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from datetime import datetime
import pandas as pd
import time
import re
import requests
from dotenv import load_dotenv
import os
import logging
load_dotenv()

logging.basicConfig(
    filename="test.log",  # Log file location
    level=logging.INFO,              # Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format="%(asctime)s - %(levelname)s - %(message)s",  # Log format
)


# Define paths and credentials
CHROMEDRIVER_PATH = r"C:\Users\SelengeTulga\Documents\chromedriver\chromedriver.exe"
LOGIN_URL = os.getenv('APPFOLIO_LOGIN_URL')
USERNAME = os.getenv('APPFOLIO_USERNAME')
PASSWORD = os.getenv('APPFOLIO_PASSWORD')
WORK_ORDER_URL = os.getenv('WORK_ORDER_URL')
VACANCY_URL = os.getenv('VACANCY_URL')

BASE_DOWNLOAD_FOLDER = r"C:\Users\SelengeTulga\Documents\GitHub\appfolio-dashboard\data"

# Define separate folders for each CSV type
TENANT_FOLDER = os.path.join(BASE_DOWNLOAD_FOLDER, "tenant_data")
WORK_ORDER_FOLDER = os.path.join(BASE_DOWNLOAD_FOLDER, "work_orders")
VACANCY_FOLDER = os.path.join(BASE_DOWNLOAD_FOLDER, "vacancies")


# SimpleTexting API Key
API_TOKEN = os.getenv('SIMPLE_TEXTING_API_TOKEN')
API_URL = os.getenv('SIMPLE_TEXTING_API_URL')
ACCOUNT_PHONE = os.getenv('SIMPLE_TEXTING_ACCOUNT_PHONE')


def get_latest_message():
    """Fetch the latest message from SimpleTexting API with retry on 429 error."""
    params = {"page": 0, "size": 1, "accountPhone": ACCOUNT_PHONE}
    headers = {"Authorization": f"Bearer {API_TOKEN}", "Accept": "application/json"}
    
    for attempt in range(3):  # Retry up to 3 times
        try:
            response = requests.get(API_URL, headers=headers, params=params)
            if response.status_code == 429:
                print("Too many requests. Waiting 10 seconds before retrying...")
                logging.info("Too many requests. Waiting 10 seconds before retrying...")
                time.sleep(10)  # Wait before retrying
                continue
            response.raise_for_status()

            messages = response.json().get("content", [])
            return messages[0] if messages else None

        except requests.RequestException as e:
            print(f"API Error: {e}")
            logging.info(f"API Error: {e}")

    print("Failed to retrieve messages after multiple attempts.")
    logging.info("Failed to retrieve messages after multiple attempts.")
    return None



def wait_for_new_code(previous_message_id):
    """Wait for a new verification code that is different from the previous one."""
    max_wait_time = 30  # Maximum time to wait (in seconds)
    wait_interval = 2  # Check every 2 seconds

    for _ in range(max_wait_time // wait_interval):
        latest_message = get_latest_message()
        if latest_message and latest_message["id"] != previous_message_id:
            match = re.search(r"\b\d{6}\b", latest_message["text"])  # Extract 6-digit code
            if match:
                return match.group(0)
        time.sleep(wait_interval)

    print(" Failed to retrieve a new verification code within the time limit.")
    logging.info(" Failed to retrieve a new verification code within the time limit.")
    return None

def click_update_button(driver):
    """Click the Columns tab, check the checkboxes, and click the Update button."""
    try:
        update_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[text()='Update']"))
        )
        update_button.click()
        print("Update button clicked successfully.")
        logging.info("Update button clicked successfully.")

    except Exception as e:
        print(f"An error occurred: {e}")
        logging.info(f"An error occurred: {e}")


def open_dropdown_and_click_csv(driver):
    """Open dropdown and click the Export CSV button, and verify if it was successful."""
    try:
        # Open the dropdown menu
        dropdown_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'dropdown-div') and contains(@class, 'js-actions-dropdown')]//button"))
        )
        dropdown_button.click()
        print("Dropdown menu opened successfully.")
        
        # Click the Export CSV button
        csv_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'js-export-csv-button')]"))
        )
        csv_button.click()
        print("Export CSV button clicked successfully.")
        logging.info("Export CSV button clicked successfully.")

        # Check if the CSV file download was triggered
        # You can use specific logic to verify download completion based on your environment
        
        print("CSV export process initiated.")
        logging.info("CSV export process initiated.")

    except Exception as e:
        print(f"An error occurred: {e}")
        logging.info(f"An error occurred: {e}")

def get_latest_csv(downloads_folder, max_wait_time=30):
    """Retrieve the latest downloaded CSV file after waiting for it."""
    print(" Waiting for CSV file to be downloaded...")
    logging.info(" Waiting for CSV file to be downloaded...")
    
    for _ in range(max_wait_time // 2):  # Check every 2 seconds, up to 30 seconds
        files = os.listdir(downloads_folder)
        csv_files = [f for f in files if f.endswith('.csv')]
        if csv_files:
            latest_file = max([os.path.join(downloads_folder, f) for f in csv_files], key=os.path.getctime)
            print(f" Latest downloaded file: {latest_file}")
            logging.info(f" Latest downloaded file: {latest_file}")
            return latest_file
        time.sleep(2)  # Wait before checking again
    
    raise FileNotFoundError(" No CSV files found in the downloads folder after waiting.")

def clean_csv(file_path):
    df = pd.read_csv(file_path)
    df = df.iloc[:-1]

    # Handle phone numbers
    df['Phone_Number'] = df['Phone Numbers'].str.split(',').str[0] 
    df['Email'] = df['Emails'].str.split(',').str[0]
    df = df.drop(columns=['Property', 'Rent', 'Tenant Type', 'Deposit', 'Tenant Tags', 'Lease To', 'Move-in','Emails', 'Phone Numbers'])
    df['Phone_Number'] = df['Phone_Number'].str.replace(r'^(Mobile:|Phone: )\s*', '', regex=True)
    df['Last_Name'] = df['Tenant'].str.split(',').str[0] 
    df['First_Name'] = df['Tenant'].str.split(',').str[1] 
    df['First_Name'] = df['First_Name'].str.upper()
    df['Last_Name'] = df['Last_Name'].str.upper()

     # If 'First_Name' is null, use 'Last_name'
    df['First_Name'] = df['First_Name'].fillna(df['Last_Name'])
    
    # Generate a timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = f'C:\\Users\\SelengeTulga\\Downloads\\Tenant\\cleaned_csv\\tenant_directory_cleaned_{timestamp}.csv'
    
    df.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"CSV saved to: {output_path}")
    logging.info(f"CSV saved to: {output_path}")

def download_csv(driver, page_url, folder, file_prefix):
    """Navigate to a page, download CSV, and move it to the correct folder."""
    logging.info(f"Navigating to {page_url} and downloading CSV...")
    driver.get(page_url)
    time.sleep(3)

    # Click update and download CSV
    click_update_button(driver)
    time.sleep(3)
    open_dropdown_and_click_csv(driver)
    time.sleep(5)

    # Retrieve latest CSV and move it to the correct folder
    downloaded_csv = get_latest_csv(BASE_DOWNLOAD_FOLDER)
    

def get_data_from_appfolio():
    logging.info("Started Appfolio data process")
    """Check if ChromeDriver is set up correctly and perform login."""
    success = False  # Initialize success flag
    # Set up Chrome options
    options = Options()
    options.add_experimental_option("prefs", {"download.default_directory": BASE_DOWNLOAD_FOLDER})  # Set default download folder
    service = Service(CHROMEDRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=options)

    # Open login page
    print("[INFO] Opening login page...")
    logging.info("[INFO] Opening login page...")
    driver.get(LOGIN_URL)

    try:
        # Wait for username field and enter credentials
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "user_email"))).send_keys(USERNAME)
        print("[INFO] Entered username")
        logging.info("[INFO] Entered username")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "user_password"))).send_keys(PASSWORD)
        print("[INFO] Entered password")
        logging.info("[INFO] Entered password")
        # Click login button
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "commit"))).click()
        print("[INFO] Clicked login button")
        logging.info("[INFO] Clicked login button")
        time.sleep(3)  # Wait for 2FA screen to load

        # Detect if 2FA is required
        if "verification_code" in driver.page_source:
            print("[INFO] 2-Step Verification detected. Retrieving verification code...")
            logging.info("[INFO] 2-Step Verification detected. Retrieving verification code...")
            # Get the latest message ID **before** requesting a new code
            previous_message = get_latest_message()
            previous_message_id = previous_message["id"] if previous_message else None

            # Click "Send Verification Code" button
            WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//input[@value='Send Verification Code']"))
            ).click()
            print("[INFO] Requested verification code.")
            logging.info("[INFO] Requested verification code.")
            # Wait for a new code that is different from the previous one
            verification_code = wait_for_new_code(previous_message_id)

            if not verification_code:
                print(" No new verification code received.")
                logging.info("No new verification code received.")
                driver.quit()
                exit()

            # Enter verification code
            verification_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "user_verification_code"))
            )
            verification_input.click()
            time.sleep(1)
            verification_input.send_keys(verification_code)
            print(f"Entered verification code: {verification_code}")
            logging.info(f"Entered verification code: {verification_code}")
            
            # Click "Sign In" Button
            sign_in_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "sign_in_button"))
            )
            sign_in_button.click()
            print("Successfully submitted the verification code!")
            logging.info("Successfully submitted the verification code!")

        else:
            print("[SUCCESS] Login successful (No 2FA required).")
            logging.info("[SUCCESS] Login successful (No 2FA required).")
        
        time.sleep(3)  # Allow page to load

       # Download Tenant Data
        tenant_csv = download_csv(driver, LOGIN_URL, TENANT_FOLDER, "tenant_data")

        # Download Work Order Data
        work_order_csv = download_csv(driver, WORK_ORDER_URL, WORK_ORDER_FOLDER, "work_order")

        # Download Vacancy Data
        vacancy_csv = download_csv(driver, VACANCY_URL, VACANCY_FOLDER, "vacancy")

        success = True  # Mark as successful
    except Exception as e:
        print(f" An error occurred: {e}")
        logging.info(f" An error occurred: {e}")

    finally:
        driver.quit()
        if success:
            logging.info("[SUCCESS] The entire process completed successfully.")
            print("[SUCCESS] The entire process completed successfully.")
        else:
            logging.info("[ERROR] The process encountered an error.")
            print("[ERROR] The process encountered an error.")
        time.sleep(3)


if __name__ == "__main__":
    get_data_from_appfolio()
    
