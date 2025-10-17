# eCourts Cause List Automation

This project automates fetching cause lists and case status from the [eCourts India portal](https://services.ecourts.gov.in/). It supports:

- CNR-based case status fetch
- Court-wise cause list fetch
- Captcha handling with Base64 for React integration
- PDF generation for cause lists
- Download all PDFs as zip

## Features

- Flask backend API
- Selenium automation in headless Chrome
- BeautifulSoup for parsing HTML tables
- pdfkit for PDF generation
- React front-end can receive captcha as Base64



## Make sure ChromeDriver is installed and path is updated in app.py:

CHROME_DRIVER_PATH = "D:/Siddhi/Jobs/ecourt cause list/chromedriver-win64/chromedriver.exe"


## Make sure wkhtmltopdf is installed and path is set correctly:

pdfkit.configuration(wkhtmltopdf=r"C:/Program Files/wkhtmltopdf/bin/wkhtmltopdf.exe")

## Usage

Run the Flask server:

python app.py

Open new terminal and change directory to frontend and run :

npm install
npm start

## API Endpoints:

/api/fetch_by_cnr_init – Initialize CNR search

/api/fetch_by_cnr_submit – Submit CNR captcha

/api/fetch_by_court_init – Initialize court fetch

/api/fetch_by_court_submit – Submit court captcha

/api/download_pdf?path=<pdf_path> – Download generated PDF