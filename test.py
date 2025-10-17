from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import json
import time

# ---------------- CONFIG ----------------
CHROME_DRIVER_PATH = r"D:/Siddhi/Jobs/ecourt cause list/chromedriver-win64/chromedriver.exe"   # path to your chromedriver
BASE_URL = "https://services.ecourts.gov.in/ecourtindia_v6/"

# ---------------- HELPERS ----------------
def parse_case_table(html_content):
    """Parse the case status table and return as dictionary"""
    soup = BeautifulSoup(html_content, "html.parser")
    table = soup.find("table", class_="case_status_table")
    if not table:
        return None

    case_info = {}
    rows = table.find_all("tr")
    for row in rows:
        label_tag = row.find("label")
        if not label_tag:
            continue
        label = label_tag.get_text(strip=True)
        value_td = row.find_all("td")[1]
        value = value_td.get_text(strip=True)
        case_info[label] = value
    return case_info

def is_listed_today_or_tomorrow(date_str):
    """Check if next hearing date is today or tomorrow"""
    try:
        date_obj = datetime.strptime(date_str, "%dth %B %Y")
        today = datetime.today().date()
        tomorrow = today + timedelta(days=1)
        return date_obj.date() in [today, tomorrow]
    except:
        return False

def save_json(data, filename):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
    print(f"[INFO] Saved data to {filename}")

# ---------------- MAIN ----------------
def main():
    cnr = input("Enter 16-digit CNR number: ").strip()

    options = Options()
    options.headless = False  # Change to True to run in background
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(service=Service(CHROME_DRIVER_PATH), options=options)
    wait = WebDriverWait(driver, 30)  # increase wait for captcha/manual intervention

    try:
        # Step 1: Open portal
        driver.get(BASE_URL)
        print("[INFO] Opened eCourts portal")
        time.sleep(2)

        # Optional: If captcha is present, pause for user
        print("[INFO] Please complete captcha manually if prompted, then press Enter here...")
        input()

        # Step 2: Wait for CNR input box
        cino_input = wait.until(
            EC.visibility_of_element_located((By.ID, "cino"))
        )
        cino_input.clear()
        cino_input.send_keys(cnr)

        # Step 3: Click search button
        # Wait for the search button to be clickable
        search_button = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.ID, "searchbtn"))
        )
        search_button.click()
        print("[INFO] Search submitted")


        # Step 4: Wait for case table to load
        case_table = wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, "case_status_table"))
        )
        html_content = driver.page_source

        # Step 5: Parse table
        case_info = parse_case_table(html_content)
        if not case_info:
            print("[INFO] No case found or table not loaded")
            return

        # Step 6: Print results
        print("\n=== Case Details ===")
        for k, v in case_info.items():
            print(f"{k}: {v}")

        # Step 7: Check next hearing date
        next_date = case_info.get("Next Hearing Date")
        if next_date and is_listed_today_or_tomorrow(next_date):
            print("[INFO] Case is listed today or tomorrow!")

        # Step 8: Save JSON
        save_json(case_info, f"case_{cnr}.json")

    finally:
        input("Press Enter to close browser...")
        driver.quit()

if __name__ == "__main__":
    main()
