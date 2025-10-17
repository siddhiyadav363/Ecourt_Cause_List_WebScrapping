from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import os, time, tempfile, zipfile, requests, traceback, pdfkit, base64

# ---------- CONFIG ----------
CHROME_DRIVER_PATH = r"D:/Siddhi/Jobs/ecourt cause list/chromedriver-win64/chromedriver.exe"
BASE_URL = "https://services.ecourts.gov.in/ecourtindia_v6/"
DOWNLOAD_DIR = os.path.join(tempfile.gettempdir(), "D:/Siddhi/Jobs/ecourt cause list/data")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

app = Flask(__name__)
CORS(app)
driver_instance = None


# ---------- Global Selenium driver for captcha session ----------
driver_sessions = {}  

def make_driver(headless=True, download_dir=None):
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1920,1080")
    if download_dir:
        prefs = {
            "download.default_directory": download_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        }
        options.add_experimental_option("prefs", prefs)
    return webdriver.Chrome(service=Service(CHROME_DRIVER_PATH), options=options)

def parse_case_table_from_html(html):
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table", class_="case_status_table")
    if not table:
        return {}
    result = {}
    for row in table.find_all("tr"):
        lbl = row.find("label")
        if not lbl:
            continue
        key = lbl.get_text(strip=True)
        tds = row.find_all("td")
        if len(tds) >= 2:
            result[key] = tds[1].get_text(strip=True)
    return result

def find_pdf_links_from_html(html):
    soup = BeautifulSoup(html, "html.parser")
    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.lower().endswith(".pdf"):
            if href.startswith("/"):
                href = "https://services.ecourts.gov.in" + href
            links.append(href)
    return links

# ------------------ CNR Fetch ------------------

@app.route("/api/fetch_by_cnr_init", methods=["POST"])
def fetch_by_cnr_init():
    payload = request.json or {}
    cnr = payload.get("cnr")
    if not cnr:
        return jsonify({"error": "CNR is required"}), 400

    try:
        driver = make_driver(headless=True, download_dir=DOWNLOAD_DIR)
        session_id = cnr  
        driver_sessions[session_id] = driver

        driver.get(BASE_URL)
        wait = WebDriverWait(driver, 20)
        time.sleep(2)

        cino_input = wait.until(EC.visibility_of_element_located((By.ID, "cino")))
        cino_input.clear()
        cino_input.send_keys(cnr)


        try:
            captcha_img = driver.find_element(By.ID, "captcha_image")
            captcha_b64 = captcha_img.screenshot_as_base64
            return jsonify({"captcha_required": True, "captcha_image": captcha_b64, "session_id": session_id})
        except:
            search_btn = wait.until(EC.element_to_be_clickable((By.ID, "searchbtn")))
            search_btn.click()
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "case_status_table")))
            html = driver.page_source
            case_info = parse_case_table_from_html(html)
            pdf_links = find_pdf_links_from_html(html)
            return jsonify({"session_id": session_id, "case_info": case_info, "pdf_links": pdf_links})
    except Exception as e:
        return jsonify({"error": str(e), "trace": traceback.format_exc()})

@app.route("/api/fetch_by_cnr_submit", methods=["POST"])
def fetch_by_cnr_submit():
    payload = request.json or {}
    captcha_text = payload.get("captcha")
    session_id = payload.get("session_id")
    download_pdf_flag = payload.get("download_pdf", True)

    if session_id not in driver_sessions:
        return jsonify({"error": "Session expired. Please restart."}), 400
    driver = driver_sessions[session_id]

    try:
        captcha_input = driver.find_element(By.ID, "fcaptcha_code")

        captcha_input.clear()
        captcha_input.send_keys(captcha_text)

        search_btn = driver.find_element(By.ID, "searchbtn")
        search_btn.click()
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CLASS_NAME, "case_status_table")))

        html = driver.page_source
        case_info = parse_case_table_from_html(html)
        pdf_links = find_pdf_links_from_html(html)
        downloaded_files = []

        if download_pdf_flag and pdf_links:
            for idx, link in enumerate(pdf_links):
                r = requests.get(link, timeout=30)
                if r.status_code == 200:
                    fname = os.path.join(DOWNLOAD_DIR, f"{session_id}_{idx}.pdf")
                    with open(fname, "wb") as f:
                        f.write(r.content)
                    downloaded_files.append(fname)

        response = {"case_info": case_info, "pdfs": [os.path.basename(f) for f in downloaded_files]}
        if downloaded_files:
            zip_path = os.path.join(DOWNLOAD_DIR, f"{session_id}_files.zip")
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
                for f in downloaded_files:
                    zf.write(f, arcname=os.path.basename(f))
            response["zip"] = os.path.basename(zip_path)

        return jsonify(response)
    except Exception as e:
        return jsonify({"error": str(e), "trace": traceback.format_exc()})
    finally:
        driver.quit()
        driver_sessions.pop(session_id, None)

# ------------------ Court Fetch ------------------

@app.route("/api/fetch_by_court_init", methods=["POST"])
def fetch_by_court_init():
    payload = request.json or {}
    session_id = payload.get("session_id") or os.urandom(8).hex()
    state = payload.get("state")
    district = payload.get("district")
    court_complex_code = payload.get("court_complex_code")
    court_name = payload.get("court_name")
    cause_date = payload.get("date")

    try:
        driver = make_driver(headless=True)
        driver_sessions[session_id] = driver
        driver.get("https://services.ecourts.gov.in/ecourtindia_v6/?p=cause_list/")
        wait = WebDriverWait(driver, 20)
        time.sleep(2)

        Select(wait.until(EC.element_to_be_clickable((By.ID, "sess_state_code")))).select_by_visible_text(state)
        Select(wait.until(EC.element_to_be_clickable((By.ID, "sess_dist_code")))).select_by_visible_text(district)
        Select(wait.until(EC.element_to_be_clickable((By.ID, "court_complex_code")))).select_by_visible_text(court_complex_code)
        wait.until( EC.presence_of_element_located( (By.XPATH, f"//select[@id='CL_court_no']/option[normalize-space(text())='{court_name}']") ) ) 
        court_name_select = wait.until(EC.element_to_be_clickable((By.ID, "CL_court_no"))) 
        Select(court_name_select).select_by_visible_text(court_name)

        date_input = wait.until(EC.visibility_of_element_located((By.ID, "causelist_date")))
        date_input.clear()
        date_input.send_keys(cause_date)

        captcha_img = wait.until(EC.presence_of_element_located((By.ID, "captcha_image")))
        captcha_b64 = captcha_img.screenshot_as_base64

        return jsonify({"captcha_image": captcha_b64, "session_id": session_id})
    except Exception as e:
        return jsonify({"error": str(e), "trace": traceback.format_exc()})

@app.route("/api/fetch_by_court_submit", methods=["POST"])
def fetch_by_court_submit():
    payload = request.json or {}
    captcha_text = payload.get("captcha")
    case_type = payload.get("case_type", "civ")
    session_id = payload.get("session_id")

    if session_id not in driver_sessions:
        return jsonify({"error": "Session expired. Please restart."}), 400

    driver = driver_sessions[session_id]

    try:
        captcha_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "cause_list_captcha_code"))
        )
        captcha_input.clear()
        captcha_input.send_keys(captcha_text)

        try:
            modal_close_btn = driver.find_element(
                By.XPATH, "//div[@id='validateError']//button[contains(text(),'Close') or @class='close']"
            )
            driver.execute_script("arguments[0].click();", modal_close_btn)
            time.sleep(0.5)
        except Exception:
            pass

        buttons = driver.find_elements(By.XPATH, "//button[contains(@onclick, 'submit_causelist')]")
        clicked = False
        for b in buttons:
            if case_type in b.get_attribute("onclick"):
                driver.execute_script("arguments[0].click();", b)
                clicked = True
                break

        if not clicked:
            return jsonify({"error": "Case type button not found"}), 400

        time.sleep(4)
        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")
        table = soup.find("table", {"id": "dispTable"})

        if not table:
            return jsonify({"error": "Cause list not found"}), 404

        pdf_path = os.path.join(DOWNLOAD_DIR, f"{session_id}_cause_list.pdf")
        config = pdfkit.configuration(
            wkhtmltopdf=r"C:/Program Files/wkhtmltopdf/bin/wkhtmltopdf.exe"
        )
        pdfkit.from_string(str(table), pdf_path, configuration=config)

        return jsonify({"message": "PDF generated successfully", "pdf_path": pdf_path})

    except Exception as e:
        return jsonify({"error": str(e), "trace": traceback.format_exc()})

    finally:
        driver.quit()
        driver_sessions.pop(session_id, None)

@app.route("/api/download_pdf", methods=["GET"])
def download_pdf():
    path = request.args.get("path")
    if not path:
        return jsonify({"error": "Missing 'path' parameter"}), 400
    return send_file(path, as_attachment=True)

if __name__ == "__main__":
    app.run(port=5000, debug=True)
