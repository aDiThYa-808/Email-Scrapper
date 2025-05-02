import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse

visited = set()
emails_found = set()

def normalize_url(url):
    parsed = urlparse(url)
    return parsed.scheme + "://" + parsed.netloc + parsed.path.rstrip("/")

def is_internal_link(base_url, link):
    return urlparse(base_url).netloc == urlparse(link).netloc

def scrape_page(url, base_url, depth=0, max_depth=2):
    if depth > max_depth:
        return

    url = normalize_url(url)
    if url in visited:
        return
    visited.add(url)

    try:
        print(f"{'  '*depth}🔍 Visiting: {url}")
        response = requests.get(url, timeout=10)

        if response.status_code != 200:
            print(f"{'  '*depth}❌ Skipped (status {response.status_code}): {url}")
            return

        soup = BeautifulSoup(response.text, "html.parser")
        text = soup.get_text()

        # Find emails
        emails = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
        for email in emails:
            if email not in emails_found:
                print(f"{'  '*depth}✅ Found email: {email}")
                emails_found.add(email)

        # Find internal links
        for link_tag in soup.find_all("a", href=True):
            href = link_tag["href"]

            if href.startswith(("mailto:", "tel:", "javascript:", "#")):
                continue
            if any(href.endswith(ext) for ext in [".pdf", ".jpg", ".jpeg", ".png", ".doc", ".docx", ".zip"]):
                continue

            full_link = urljoin(url, href)
            if is_internal_link(base_url, full_link):
                scrape_page(full_link, base_url, depth + 1, max_depth)

    except Exception as e:
        print(f"{'  '*depth}⚠️ Error at {url} — {e}")

# 🔧 START HERE
start_url = "https://americancollege.edu.in"  # Try small site first
print(f"\nScraping emails from {start_url}...\n")
scrape_page(start_url, start_url)

print("\n📧 Found emails:")
for email in emails_found:
    print(" -", email)
