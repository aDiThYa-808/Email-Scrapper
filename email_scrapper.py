import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re
import fitz  # PyMuPDF

def extract_emails_from_text(text):
    return set(re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text))

def extract_emails_from_pdf_url(pdf_url):
    try:
        response = requests.get(pdf_url, timeout=10)
        if response.status_code == 200 and 'application/pdf' in response.headers.get('Content-Type', ''):
            with fitz.open(stream=response.content, filetype="pdf") as doc:
                text = ""
                for page in doc:
                    text += page.get_text()
            return extract_emails_from_text(text)
    except Exception as e:
        print(f"⚠️ PDF error at {pdf_url} — {e}")
    return set()

def scrape_single_page(url):
    print(f"🔍 Scanning: {url}")
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            print("❌ Could not load the page.")
            return

        soup = BeautifulSoup(response.text, "html.parser")

        # Emails from page text
        text_emails = extract_emails_from_text(soup.get_text())

        # Emails from PDFs linked on this page
        pdf_emails = set()
        for tag in soup.find_all("a", href=True):
            href = tag["href"]
            if href.endswith(".pdf"):
                full_pdf_url = urljoin(url, href)
                print(f"📄 Found PDF: {full_pdf_url}")
                pdf_emails.update(extract_emails_from_pdf_url(full_pdf_url))

        all_emails = text_emails.union(pdf_emails)
        print("\n✅ Found email(s):")
        for email in all_emails:
            print(" -", email)

    except Exception as e:
        print(f"⚠️ Error scraping page: {e}")

# ▶️ Example usage
scrape_single_page("https://americancollege.edu.in/bio-technology-faculty/")
