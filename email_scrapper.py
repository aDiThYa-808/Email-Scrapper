import requests
from bs4 import BeautifulSoup
import csv
import time
import os
from datetime import datetime
from urllib.parse import urljoin

# Configuration
BASE_URL = "https://www.ncbs.res.in"
FACULTY_LIST_URL = "https://www.ncbs.res.in/faculty"  # Update this to the actual faculty listing page
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
DELAY_BETWEEN_REQUESTS = 2  # seconds to be respectful to the server
TIMEOUT = 30  # increased timeout
MAX_RETRIES = 3

def log_message(message, log_file="scraping_logs.txt"):
    """Log messages with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"[{timestamp}] {message}\n")
    print(f"[{timestamp}] {message}")

def convert_obfuscated_email(obfuscated_email):
    """Convert obfuscated email format to proper email"""
    if not obfuscated_email:
        return None
    
    # Replace 'at' with '@' and 'dot' with '.'
    email = obfuscated_email.replace(" at ", "@").replace(" dot ", ".")
    # Handle case variations
    email = email.replace(" AT ", "@").replace(" DOT ", ".")
    # Remove extra spaces
    email = email.strip()
    return email

def make_request_with_retry(url, max_retries=MAX_RETRIES):
    """Make HTTP request with retry logic"""
    for attempt in range(max_retries):
        try:
            log_message(f"Attempting to connect to {url} (attempt {attempt + 1}/{max_retries})")
            response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
            response.raise_for_status()
            return response
        except requests.exceptions.Timeout:
            log_message(f"Timeout on attempt {attempt + 1}")
            if attempt < max_retries - 1:
                time.sleep(5)  # Wait before retry
            else:
                raise
        except requests.exceptions.RequestException as e:
            log_message(f"Request failed on attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                time.sleep(5)
            else:
                raise

def test_connection():
    """Test basic connectivity to the website"""
    log_message("Testing basic connectivity...")
    test_urls = [
        "https://www.ncbs.res.in",
        "https://www.ncbs.res.in/faculty",
        "https://www.ncbs.res.in/faculty/mini-contact"
    ]
    
    for url in test_urls:
        try:
            response = make_request_with_retry(url)
            log_message(f"✓ Successfully connected to {url} - Status: {response.status_code}")
            # Print first 200 characters to see what we get
            soup = BeautifulSoup(response.text, 'html.parser')
            preview = soup.get_text()[:200].replace('\n', ' ').strip()
            log_message(f"Preview: {preview}...")
        except Exception as e:
            log_message(f"✗ Failed to connect to {url}: {e}")

def get_faculty_names():
    """Scrape all faculty names from the main faculty listing page"""
    log_message("Starting to scrape faculty names from listing page...")
    
    try:
        response = make_request_with_retry(FACULTY_LIST_URL)
        
        soup = BeautifulSoup(response.text, 'html.parser')
        faculty_names = []
        
        # You'll need to update this selector based on the actual HTML structure
        # This is a placeholder - inspect the faculty listing page to find the right selector
        faculty_links = soup.find_all('a', href=True)
        
        for link in faculty_links:
            href = link.get('href', '')
            # Look for links that match the pattern /faculty/name-contact or /faculty/name
            if '/faculty/' in href and href != '/faculty/':
                # Extract faculty name from URL
                faculty_name = href.split('/faculty/')[-1]
                # Remove '-contact' suffix if present
                faculty_name = faculty_name.replace('-contact', '')
                # Remove any other suffixes or clean the name
                faculty_name = faculty_name.strip('/')
                
                if faculty_name and faculty_name not in faculty_names:
                    faculty_names.append(faculty_name)
        
        log_message(f"Found {len(faculty_names)} faculty names")
        return faculty_names
        
    except Exception as e:
        log_message(f"Error getting faculty names: {e}")
        return []

def scrape_faculty_email(faculty_name):
    """Scrape email from individual faculty contact page"""
    contact_url = f"{BASE_URL}/faculty/{faculty_name}-contact"
    
    try:
        response = make_request_with_retry(contact_url)
        
        # Store the URL
        with open('urls.txt', 'a', encoding='utf-8') as f:
            f.write(f"{contact_url}\n")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        page_text = soup.get_text()
        
        # Look for obfuscated email patterns
        # This regex looks for patterns like "name at domain dot extension"
        import re
        email_pattern = r'[a-zA-Z0-9._%+-]+\s+at\s+[a-zA-Z0-9.-]+\s+dot\s+[a-zA-Z]+(?:\s+dot\s+[a-zA-Z]+)*'
        
        matches = re.findall(email_pattern, page_text, re.IGNORECASE)
        
        if matches:
            # Take the first match and convert it
            obfuscated_email = matches[0]
            proper_email = convert_obfuscated_email(obfuscated_email)
            log_message(f"Found email for {faculty_name}: {proper_email}")
            return proper_email
        else:
            log_message(f"No email found for {faculty_name}")
            return None
            
    except requests.exceptions.RequestException as e:
        if e.response and e.response.status_code == 404:
            log_message(f"Faculty page not found (404): {contact_url}")
        else:
            log_message(f"Error scraping {faculty_name}: {e}")
        return None
    except Exception as e:
        log_message(f"Unexpected error scraping {faculty_name}: {e}")
        return None

def save_to_csv(college_name, faculty_name, email, csv_file="emails.csv"):
    """Save faculty data to CSV file"""
    file_exists = os.path.isfile(csv_file)
    
    with open(csv_file, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Write headers if file doesn't exist
        if not file_exists:
            writer.writerow(['college_name', 'faculty_name', 'email'])
        
        writer.writerow([college_name, faculty_name, email])

def main():
    """Main scraping function"""
    log_message("Starting NCBS faculty email scraping...")
    
    # Test connection first
    test_connection()
    
    # Get all faculty names
    faculty_names = get_faculty_names()
    
    if not faculty_names:
        log_message("No faculty names found. Please check the faculty listing URL and HTML structure.")
        return
    
    college_name = "ncbs"
    successful_scrapes = 0
    
    # Scrape each faculty member
    for i, faculty_name in enumerate(faculty_names, 1):
        log_message(f"Processing faculty {i}/{len(faculty_names)}: {faculty_name}")
        
        email = scrape_faculty_email(faculty_name)
        
        if email:
            save_to_csv(college_name, faculty_name, email)
            successful_scrapes += 1
        
        # Be respectful to the server
        if i < len(faculty_names):  # Don't delay after the last request
            time.sleep(DELAY_BETWEEN_REQUESTS)
    
    log_message(f"Scraping completed! Successfully scraped {successful_scrapes}/{len(faculty_names)} faculty emails.")
    log_message(f"Results saved to emails.csv")
    log_message(f"URLs saved to urls.txt")
    log_message(f"Logs saved to scraping_logs.txt")

if __name__ == "__main__":
    main()