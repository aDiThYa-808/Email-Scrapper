#simple scrapper that scrapes emails from webpages with simple structure and no ofuscation
import requests
from bs4 import BeautifulSoup
import re
import csv

# === Config ===
url = "https://www.drngpasc.ac.in/best-arts-college-for-bsc-clinical-laboratory-technology-in-coimbatore-tamilnadu"
college_name = "Dr. N.G.P. Arts and Science College"
output_file = "emails.csv"

def extract_emails(text):
    text = text.replace('[at]', '@').replace('(at)', '@')
    text = text.replace('[dot]', '.').replace('(dot)', '.')
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[a-z]{2,}\b'
    return list(set(re.findall(email_pattern, text)))

def scrape_emails(url, college_name):
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
    except Exception as e:
        print(f"Failed to fetch {url}: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    raw_text = soup.get_text()
    emails = extract_emails(raw_text)

    results = []
    for email in emails:
        match_elem = soup.find(string=re.compile(re.escape(email)))
        if match_elem:
            strong_tag = match_elem.find_previous('strong')
            name = strong_tag.get_text(strip=True) if strong_tag else "N/A"
        else:
            name = "N/A"

        results.append((college_name, name, email))
    return results

def save_to_csv(rows, filename):
    with open(filename, "a", newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(rows)

# === Run ===
data = scrape_emails(url, college_name)
save_to_csv(data, output_file)

print(f"✓ Appended {len(data)} emails to {output_file}")
