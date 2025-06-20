#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup

# Test a few URLs to understand the response patterns
test_urls = [
    "https://vsdigital-bookingwidget-prod.azurewebsites.net/widget-business/aa00a",  # Should be invalid
    "https://vsdigital-bookingwidget-prod.azurewebsites.net/widget-business/tc33l",  # Known good
]

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
})

for url in test_urls:
    print(f"\n{'='*50}")
    print(f"Testing: {url}")
    print(f"{'='*50}")
    
    try:
        response = session.get(url, timeout=10, allow_redirects=True)
        print(f"Status Code: {response.status_code}")
        print(f"Final URL: {response.url}")
        print(f"Content Length: {len(response.text)}")
        
        # Show first 1000 characters
        print(f"\nFirst 1000 characters:")
        print(response.text[:1000])
        
        # Parse with BeautifulSoup to find specific elements
        soup = BeautifulSoup(response.text, 'html.parser')
        title = soup.find('title')
        if title:
            print(f"\nTitle: {title.get_text().strip()}")
        
        # Look for specific indicators
        if 'booking' in response.text.lower():
            print("✅ Contains 'booking'")
        if 'error' in response.text.lower():
            print("❌ Contains 'error'")
        if 'not found' in response.text.lower():
            print("❌ Contains 'not found'")
        if 'unauthorized' in response.text.lower():
            print("❌ Contains 'unauthorized'")
            
    except Exception as e:
        print(f"Error: {e}") 