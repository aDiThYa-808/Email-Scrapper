import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse
import fitz  # PyMuPDF
import io

# Set
MAX_PAGES = 100  # Max number of pages to crawl
MAX_DEPTH = 3    # Max depth level to avoid too deep crawling
EMAIL_REGEX = r"[a-zA-Z0-9._%+-]+@[a-zAZ0-9.-]+\.[a-zA-Z]{2,}"
HEADERS = {"User-Agent": "Mozilla/5.0"}

def extract_emails(text):
    return re.findall(EMAIL_REGEX, text)

def extract_emails_from_pdf(pdf_bytes):
    try:
        pdf = fitz.open(stream=pdf_bytes, filetype="pdf")
        text = ""
        for page in pdf:
            text += page.get_text()
        pdf.close()
        return extract_emails(text)
    except Exception as e:
        print(f"⚠️ Error reading PDF: {e}")
        return []

def is_internal_link(link, base_netloc):
    return urlparse(link).netloc in ("", base_netloc)

def normalize_url(url):
    """Normalize URL by removing fragments and trailing slashes."""
    parsed = urlparse(url)
    normalized = parsed._replace(fragment="", query="")
    clean_path = normalized.path.rstrip("/")
    return f"{normalized.scheme}://{normalized.netloc}{clean_path}"

def scrape_website(start_url):
    visited_urls = set()
    to_visit = [(start_url, 0)]  # (URL, depth)
    all_emails = {}
    visited_count = 0
    base_netloc = urlparse(start_url).netloc

    while to_visit and visited_count < MAX_PAGES:
        current_url, depth = to_visit.pop(0)

        if depth > MAX_DEPTH:
            continue  # Skip crawling if depth exceeds the maximum limit

        # Normalize the URL to avoid duplicate pages with different URL formats
        normalized_url = normalize_url(current_url)

        if normalized_url in visited_urls:
            continue

        print(f"\n🔍 Visiting ({visited_count+1}/{MAX_PAGES}): {current_url} (Depth {depth})")
        visited_urls.add(normalized_url)
        visited_count += 1

        try:
            response = requests.get(current_url, headers=HEADERS, timeout=10)
            content_type = response.headers.get("Content-Type", "")

            if "application/pdf" in content_type:
                emails = extract_emails_from_pdf(response.content)
                if emails:
                    all_emails[normalized_url] = emails
                else:
                    print("📄 PDF found but no emails.")
                continue

            soup = BeautifulSoup(response.text, "html.parser")
            page_text = soup.get_text()
            emails = extract_emails(page_text)

            if emails:
                all_emails[normalized_url] = list(set(emails))

            # Find and queue internal links for further crawling
            for link_tag in soup.find_all("a", href=True):
                href = link_tag["href"]
                full_url = urljoin(current_url, href)

                if full_url.startswith("mailto:"):
                    mail = full_url.replace("mailto:", "")
                    if normalized_url not in all_emails:
                        all_emails[normalized_url] = []
                    all_emails[normalized_url].append(mail)
                    continue

                if full_url not in visited_urls and is_internal_link(full_url, base_netloc):
                    to_visit.append((full_url, depth + 1))  # Increase depth by 1

        except Exception as e:
            print(f"⚠️ Error at {current_url} — {e}")

    return all_emails


# ==== Run the scraper ====
start_url = "https://www.sju.edu.in/faculty-members"  # Change this to your target site
emails_by_page = scrape_website(start_url)

print("\n📬 Emails found:\n")
for page, emails in emails_by_page.items():
    print(f"🔗 {page}")
    for email in set(emails):
        print(f"   📧 {email}")
