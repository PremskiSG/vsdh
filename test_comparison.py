#!/usr/bin/env python3
"""
Quick test to compare known working slug vs discovered slugs
"""

import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

def test_slug(slug, description):
    print(f"\n🔍 Testing {slug} ({description})")
    
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    driver = webdriver.Chrome(options=options)
    
    try:
        url = f"https://vsdigital-bookingwidget-prod.azurewebsites.net/widget-business/{slug}"
        print(f"Loading: {url}")
        
        driver.get(url)
        time.sleep(10)  # Wait for React to load
        
        final_url = driver.current_url
        page_title = driver.title
        body_text = driver.find_element(By.TAG_NAME, 'body').text[:200]
        
        print(f"Final URL: {final_url}")
        print(f"Page Title: '{page_title}'")
        print(f"Body Text: {body_text}")
        
        # Check for specific content
        if "401" in body_text or "ERROR" in body_text:
            print("❌ Shows error page")
        elif "Hotel" in body_text or "booking" in body_text.lower():
            print("✅ Shows business content")
        else:
            print("⚠️  Unknown content")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    # Test known working slug
    test_slug("tc33l", "Known working - Hotel Capricorn")
    
    # Test one of our discovered slugs
    test_slug("yc92e", "Discovered slug")
    
    # Test another known slug from the original list
    test_slug("ad31y", "Known original slug") 