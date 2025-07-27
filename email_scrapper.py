import requests
from bs4 import BeautifulSoup
import csv
import time
import os
import re
from datetime import datetime
from urllib.parse import urljoin, urlparse

# Configuration
BASE_URL = "https://mcb.iisc.ac.in"
FACULTY_LIST_URL = "https://mcb.iisc.ac.in/faculties"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
DELAY_BETWEEN_REQUESTS = 2  # seconds to be respectful to the server
TIMEOUT = 30
MAX_RETRIES = 3

def log_message(message, log_file="scraping_logs.txt"):
    """Log messages with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"[{timestamp}] {message}\n")
    print(f"[{timestamp}] {message}")

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
                time.sleep(5)
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
        "https://mcb.iisc.ac.in",
        "https://mcb.iisc.ac.in/faculties",
        "https://mcb.iisc.ac.in/research-single/n-ravi-sundaresan"  # Example faculty page
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
        
        # Look for links that point to research-single pages
        faculty_links = soup.find_all('a', href=True)
        
        for link in faculty_links:
            href = link.get('href', '')
            
            # Check if this is a research-single link
            if '/research-single/' in href:
                # Extract faculty name from URL
                faculty_name = href.split('/research-single/')[-1].strip('/')
                
                if faculty_name and faculty_name not in faculty_names:
                    faculty_names.append(faculty_name)
                    log_message(f"Found faculty: {faculty_name}")
        
        # Also check for any relative URLs that might be just the faculty name
        for link in faculty_links:
            href = link.get('href', '')
            if href.startswith('research-single/'):
                faculty_name = href.split('research-single/')[-1].strip('/')
                if faculty_name and faculty_name not in faculty_names:
                    faculty_names.append(faculty_name)
                    log_message(f"Found faculty (relative URL): {faculty_name}")
        
        log_message(f"Total unique faculty names found: {len(faculty_names)}")
        return faculty_names
        
    except Exception as e:
        log_message(f"Error getting faculty names: {e}")
        return []

def extract_emails_from_text(text):
    """Extract all email addresses from text"""
    # Regular expression to find email addresses
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, text)
    return list(set(emails))  # Remove duplicates

def scrape_faculty_emails(faculty_name):
    """Scrape emails from individual faculty research page"""
    research_url = f"{BASE_URL}/research-single/{faculty_name}"
    
    try:
        response = make_request_with_retry(research_url)
        
        # Store the URL for reference
        with open('urls.txt', 'a', encoding='utf-8') as f:
            f.write(f"{research_url}\n")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Get all text from the page
        page_text = soup.get_text()
        
        # Extract all emails from the page
        emails = extract_emails_from_text(page_text)
        
        if emails:
            log_message(f"Found {len(emails)} email(s) for {faculty_name}: {', '.join(emails)}")
            return emails
        else:
            log_message(f"No emails found for {faculty_name}")
            return []
            
    except requests.exceptions.RequestException as e:
        if e.response and e.response.status_code == 404:
            log_message(f"Faculty page not found (404): {research_url}")
        else:
            log_message(f"Error scraping {faculty_name}: {e}")
        return []
    except Exception as e:
        log_message(f"Unexpected error scraping {faculty_name}: {e}")
        return []

def save_to_csv(college_name, faculty_name, email, email_type, csv_file="emails.csv"):
    """Save faculty data to CSV file"""
    file_exists = os.path.isfile(csv_file)
    
    with open(csv_file, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Write headers if file doesn't exist
        if not file_exists:
            writer.writerow(['college_name', 'faculty_name', 'email', 'email_type'])
        
        writer.writerow([college_name, faculty_name, email, email_type])

def categorize_email(email, faculty_name):
    """Try to determine if email belongs to faculty or student"""
    email_lower = email.lower()
    faculty_name_parts = faculty_name.lower().replace('-', ' ').split()
    
    # Check if any part of faculty name appears in email
    for part in faculty_name_parts:
        if len(part) > 2 and part in email_lower:
            return "faculty"
    
    # Check for common patterns that might indicate faculty vs student
    if any(word in email_lower for word in ['prof', 'dr', 'faculty']):
        return "faculty"
    elif any(word in email_lower for word in ['student', 'phd', 'msc', 'bsc']):
        return "student"
    else:
        return "unknown"

def main():
    """Main scraping function"""
    log_message("Starting IISc MCB faculty email scraping...")
    
    # Test connection first
    test_connection()
    
    # Get all faculty names
    faculty_names = get_faculty_names()
    
    if not faculty_names:
        log_message("No faculty names found. Please check the faculty listing URL and HTML structure.")
        return
    
    college_name = "iisc_mcb"
    successful_scrapes = 0
    total_emails = 0
    
    # Scrape each faculty member
    for i, faculty_name in enumerate(faculty_names, 1):
        log_message(f"Processing faculty {i}/{len(faculty_names)}: {faculty_name}")
        
        emails = scrape_faculty_emails(faculty_name)
        
        if emails:
            successful_scrapes += 1
            for email in emails:
                email_type = categorize_email(email, faculty_name)
                save_to_csv(college_name, faculty_name, email, email_type)
                total_emails += 1
        
        # Be respectful to the server
        if i < len(faculty_names):  # Don't delay after the last request
            time.sleep(DELAY_BETWEEN_REQUESTS)
    
    log_message(f"Scraping completed!")
    log_message(f"Successfully scraped from {successful_scrapes}/{len(faculty_names)} faculty pages.")
    log_message(f"Total emails collected: {total_emails}")
    log_message(f"Results saved to emails.csv")
    log_message(f"URLs saved to urls.txt")
    log_message(f"Logs saved to scraping_logs.txt")

def debug_single_faculty(faculty_name):
    """Debug function to test scraping a single faculty member"""
    log_message(f"Debug mode: Testing single faculty - {faculty_name}")
    emails = scrape_faculty_emails(faculty_name)
    print(f"Emails found: {emails}")
    
    # Also print the page content for manual inspection
    research_url = f"{BASE_URL}/research-single/{faculty_name}"
    try:
        response = make_request_with_retry(research_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Save page content for inspection
        with open(f'debug_{faculty_name}.html', 'w', encoding='utf-8') as f:
            f.write(soup.prettify())
        
        log_message(f"Page content saved to debug_{faculty_name}.html")
        
    except Exception as e:
        log_message(f"Error in debug mode: {e}")

if __name__ == "__main__":
    # Uncomment the line below to test with a single faculty member first
    # debug_single_faculty("n-ravi-sundaresan")
    
    # Run the main scraper
    main()