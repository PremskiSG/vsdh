#!/usr/bin/env python3
"""
Improved test script for NzE0 with cache-busting and enhanced loading
"""

import time
import random
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def test_nze0_improved():
    # Setup Chrome driver with cache-busting options
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    
    # CACHE-BUSTING OPTIONS
    chrome_options.add_argument('--disable-cache')
    chrome_options.add_argument('--disable-application-cache')
    chrome_options.add_argument('--disable-offline-load-stale-cache')
    chrome_options.add_argument('--disk-cache-size=0')
    chrome_options.add_argument('--media-cache-size=0')
    chrome_options.add_argument('--disable-background-networking')
    chrome_options.add_argument('--disable-background-timer-throttling')
    chrome_options.add_argument('--disable-backgrounding-occluded-windows')
    chrome_options.add_argument('--disable-renderer-backgrounding')
    
    # Force fresh session
    user_data_dir = f"/tmp/chrome_test_{random.randint(1000, 9999)}_{int(time.time())}"
    chrome_options.add_argument(f'--user-data-dir={user_data_dir}')
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.set_page_load_timeout(20)  # Increased timeout
    
    try:
        slug = "NzE0"
        
        # Add cache-busting parameter with timestamp
        cache_buster = int(time.time() * 1000)
        url = f"https://vsdigital-bookingwidget-prod.azurewebsites.net/b/{slug}?cb={cache_buster}"
        
        print(f"🔍 Testing URL: {url}")
        print(f"⏰ Timestamp: {datetime.now().isoformat()}")
        
        # Clear any existing cache
        driver.execute_cdp_cmd('Network.clearBrowserCache', {})
        driver.execute_cdp_cmd('Network.clearBrowserCookies', {})
        
        # Random delay to avoid rate limiting
        delay = random.uniform(1.0, 3.0)
        print(f"⏳ Random delay: {delay:.2f}s")
        time.sleep(delay)
        
        start_time = time.time()
        driver.get(url)
        
        # Enhanced waiting strategy
        print("⏳ Waiting for page to fully load...")
        
        # Wait for document ready
        WebDriverWait(driver, 20).until(
            lambda driver: driver.execute_script("return document.readyState") == "complete"
        )
        
        # Additional wait for dynamic content
        time.sleep(3)  # Give time for any JavaScript to execute
        
        # Try to wait for specific elements that indicate page is loaded
        try:
            WebDriverWait(driver, 10).until(
                lambda driver: len(driver.page_source) > 10000
            )
        except:
            print("⚠️  Timeout waiting for substantial content, proceeding...")
        
        load_time = time.time() - start_time
        
        # Get page information
        page_title = driver.title
        final_url = driver.current_url
        page_source = driver.page_source
        content_length = len(page_source)
        
        print(f"📍 Final URL: {final_url}")
        print(f"📄 Page Title: '{page_title}'")
        print(f"📏 Content Length: {content_length}")
        print(f"⏱️  Load Time: {load_time:.2f}s")
        
        # Check for specific business indicators
        source_lower = page_source.lower()
        print(f"\n🔍 Content Analysis:")
        
        business_names_found = []
        if 'von health' in source_lower:
            business_names_found.append('Von Health')
        if 'dr frank' in source_lower or 'frank' in source_lower:
            business_names_found.append('Dr Frank')
        if 'covery' in source_lower:
            business_names_found.append('The Covery')
        if 'dripbar' in source_lower:
            business_names_found.append('DRIPBaR')
        
        if business_names_found:
            print(f"   🏢 Business names found: {', '.join(business_names_found)}")
        else:
            print(f"   ❓ No specific business names detected")
        
        # Check redirect behavior
        if url.split('?')[0] != final_url:  # Remove cache buster for comparison
            print(f"   �� REDIRECT detected!")
            if '/widget-business/' in final_url:
                widget_slug = final_url.split('/')[-1]
                print(f"   📱 Widget business slug: {widget_slug}")
        else:
            print(f"   📍 NO REDIRECT - stayed on same page")
        
        # Extract business name using same logic as collector
        business_name = ""
        if 'dripbar' in source_lower:
            if 'direct' in source_lower:
                business_name = "The DRIPBaR Direct - Location"
            else:
                business_name = "The DRIPBaR"
        elif page_title and len(page_title) > 3 and page_title.lower() not in ['', 'loading', 'error', 'undefined']:
            business_name = page_title
        
        print(f"   🏷️  Extracted business name: '{business_name}'")
        
        # Show first 2000 characters of page source for debugging
        print(f"\n📝 First 2000 chars of page source:")
        print("-" * 80)
        print(page_source[:2000])
        print("-" * 80)
        
        # Look for title tag specifically
        import re
        title_match = re.search(r'<title[^>]*>([^<]+)</title>', page_source, re.IGNORECASE)
        if title_match:
            title_content = title_match.group(1).strip()
            print(f"🏷️  Title tag content: '{title_content}'")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        driver.quit()
        
        # Clean up temp directory
        import shutil
        import os
        if 'user_data_dir' in locals() and os.path.exists(user_data_dir):
            try:
                shutil.rmtree(user_data_dir)
            except:
                pass

if __name__ == "__main__":
    test_nze0_improved()
