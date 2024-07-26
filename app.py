import os
import time
import logging
import random
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from flask import Flask, request, jsonify
from twilio.rest import Client

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Path to chromedriver
chromedriver_path = '/app/.chromedriver/bin/chromedriver'

# Twilio credentials
account_sid = 'YOUR_TWILIO_ACCOUNT_SID'
auth_token = 'YOUR_TWILIO_AUTH_TOKEN'
client = Client(account_sid, auth_token)

def send_sms(body, to):
    client.messages.create(
        body=body,
        from_='YOUR_TWILIO_PHONE_NUMBER',
        to=to
    )

def fetch_latest_sms():
    response = requests.get('http://your-ngrok-url.ngrok.io/code')
    return response.text if response.status_code == 200 else None

@app.route('/sms', methods=['POST'])
def sms_reply():
    message_body = request.form['Body'].strip().lower()
    if message_body == 'kod':
        try:
            new_code = update_verisure_code()
            return f"New house code generated and updated: {new_code}"
        except Exception as e:
            logging.error(e)
            return "Failed to generate and update the new house code."
    else:
        return "Unknown command."

def update_verisure_code():
    # Generate a new random 6-digit code
    new_code = str(random.randint(100000, 999999))
    logging.info(f"Generated new code: {new_code}")

    # Set up the Chrome driver
    service = Service(chromedriver_path)
    options = webdriver.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-blink-features=AutomationControlled')

    driver = webdriver.Chrome(service=service, options=options)

    try:
        # Open the Verisure login page
        driver.get('https://mypages.verisure.com')
        logging.info("Opened Verisure login page")

        # Click on "Sverige"
        sverige_button = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//span[@class='flag-page-box-label-box' and text()='Sverige']"))
        )
        sverige_button.click()
        logging.info("Clicked on 'Sverige'")

        # Enter username
        username_input = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "mypages-login-email"))
        )
        username_input.send_keys('YOUR_EMAIL')
        logging.info("Entered username")

        # Enter password
        password_input = driver.find_element(By.ID, 'mypages-login-password')
        password_input.send_keys('YOUR_PASSWORD')
        logging.info("Entered password")

        # Click login button
        login_button = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, '//button[@id="mypages-login-submit"]'))
        )
        login_button.click()
        logging.info("Clicked login button")

        # Switch to the specific home (Sälstensgränd)
        home_dropdown_button = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//button[@id='header-installation-menu']"))
        )
        home_dropdown_button.click()
        logging.info("Opened home dropdown menu")

        salstensgrand_option = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//div[@class='InstallationMenu_list-item__3JhsX']//p[contains(text(), 'Sälstensgränd')]"))
        )
        salstensgrand_option.click()
        logging.info("Switched to Sälstensgränd home")

        # Go to the user codes page
        users_menu = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, 'usersMenu'))
        )
        users_menu.click()
        logging.info("Accessed user code management page")

        # Scroll down and click 'Koder och brickor'
        driver.execute_script("window.scrollBy(0, 1000);")
        time.sleep(1)  # Wait to observe scrolling

        codes_and_tags = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//div[@id='codesAndTags-18627035-1']"))
        )
        codes_and_tags.click()
        logging.info("Clicked on 'Koder och brickor'")

        # Click 'Användarkod'
        user_code = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//div[@id='userCode-18627035-1']"))
        )
        user_code.click()
        logging.info("Clicked on 'Användarkod'")

        # Enter new code
        code_input = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "codeInput"))
        )
        code_input.send_keys(new_code)
        logging.info(f"Entered new code: {new_code}")

        # Click 'Spara' button
        save_button = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, 'saveCodeButton'))
        )
        save_button.click()
        logging.info("Clicked 'Spara' button")

        # Enter password again
        password_input = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "passwordInput"))
        )
        password_input.send_keys('YOUR_PASSWORD')
        logging.info("Re-entered password")

        # Click 'Skicka SMS' button
        send_sms_button = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "passwordButton"))
        )
        send_sms_button.click()
        logging.info("Clicked 'Skicka SMS' button")

        # Fetch the latest SMS containing the verification code
        verification_code = fetch_latest_sms()
        if verification_code:
            logging.info(f"Fetched verification code: {verification_code}")
        else:
            raise ValueError("Failed to fetch the verification code from SMS.")

        # Enter the verification code
        token_input = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "tokenInput"))
        )
        token_input.send_keys(verification_code)
        logging.info("Entered verification code")

        # Click 'Verifiera' button to finalize the process
        verify_button = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "tokenButton"))
        )
        verify_button.click()
        logging.info("Clicked 'Verifiera' button")

        # Notify via SMS
        send_sms(f"New house code successfully updated: {new_code}", 'YOUR_PHONE_NUMBER')
        logging.info("New house code sent via SMS")

        return new_code

    finally:
        driver.quit()
        logging.info("Closed the browser")

if __name__ == "__main__":
    app.run(debug=True)