import requests
from bs4 import BeautifulSoup
import re

# Function to scrape emails from a webpage
def scrape_emails_from_url(url):
    try:
        # Send a request to the URL
        response = requests.get(url, timeout=10)
        
        # Check if the request was successful
        if response.status_code == 200:
            # Parse the HTML content
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract all text from the page
            text = soup.get_text()
            
            # Use regex to find all emails in the text
            emails = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
            
            # Clean up the emails list: strip unwanted characters like spaces or extra text
            cleaned_emails = [email.strip() for email in emails]
            
            # Remove duplicates by converting to a set, then back to a list
            unique_emails = list(set(cleaned_emails))
            
            return unique_emails
        else:
            print(f"Error: Unable to access {url} (Status code: {response.status_code})")
            return []
    
    except requests.exceptions.RequestException as e:
        # Handle exceptions such as connection errors
        print(f"Error scraping {url}: {e}")
        return []

# Test the scraper with any website URL
if __name__ == "__main__":
    test_url = "https://cervam.co.in"  # Replace with a real biotech website URL
    emails = scrape_emails_from_url(test_url)
    
    print(f"\nFound {len(emails)} email(s):")
    for email in emails:
        print(email)
