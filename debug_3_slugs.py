#!/usr/bin/env python3
"""
Debug Script for 3 Specific Slugs
Tests NzAz, NzE5, NzE2 with enhanced debugging to see why they were marked INACTIVE
"""

import time
import base64
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import json
import os
from datetime import datetime

class SlugDebugger:
    def __init__(self):
        self.base_url = "https://vsdigital-bookingwidget-prod.azurewebsites.net/b/"
        self.timeout = 15  # Longer timeout for debugging
        self.driver = None
        
        # Test slugs that should have businesses
        self.test_slugs = ["NzAz", "NzE5", "NzE2"]  # 703, 719, 716
        
        # Current scanner indicators
        self.error_indicators = [
            '401', 'error', 'nothing left to do here', 'go to homepage',
            'not found', 'access denied', 'unauthorized',
            "the link you've opened isn't working as expected",
            'page not found', 'invalid request', 'session expired',
            'service unavailable', 'temporarily unavailable'
        ]
        
        self.business_indicators = [
            'book', 'appointment', 'schedule', 'service', 'therapy',
            'treatment', 'consultation', 'booking', 'available',
            'select', 'choose', 'weight loss', 'injection', 'iv therapy',
            'dripbar', 'semaglutide', 'tirzepatide', 'hormone',
            'wellness', 'health', 'medical', 'clinic',
            'provider', 'patient', 'visit', 'care'
        ]
    
    def setup_driver(self):
        """Setup Chrome driver for debugging"""
        chrome_options = Options()
        # Run headless for debugging
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-extensions')
        
        try:
            # Try multiple approaches
            try:
                # First try: Use webdriver_manager
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
            except Exception as e1:
                print(f"⚠️  WebDriver Manager failed: {e1}")
                try:
                    # Second try: Use system Chrome driver
                    self.driver = webdriver.Chrome(options=chrome_options)
                except Exception as e2:
                    print(f"⚠️  System Chrome driver failed: {e2}")
                    # Third try: Use explicit path (common locations)
                    chrome_paths = [
                        '/usr/local/bin/chromedriver',
                        '/opt/homebrew/bin/chromedriver',
                        '/usr/bin/chromedriver'
                    ]
                    driver_found = False
                    for path in chrome_paths:
                        if os.path.exists(path):
                            service = Service(path)
                            self.driver = webdriver.Chrome(service=service, options=chrome_options)
                            driver_found = True
                            break
                    if not driver_found:
                        raise Exception("No Chrome driver found in common locations")
            
            self.driver.set_page_load_timeout(self.timeout)
            print("✅ Chrome driver initialized for debugging")
            return True
        except Exception as e:
            print(f"❌ Failed to initialize Chrome driver: {e}")
            print("💡 Try installing Chrome driver: brew install chromedriver")
            return False
    
    def decode_slug(self, slug):
        """Decode base64 slug to see what number it represents"""
        try:
            decoded = base64.b64decode(slug).decode('utf-8')
            return decoded
        except:
            return "DECODE_ERROR"
    
    def debug_slug(self, slug):
        """Debug a single slug with comprehensive analysis"""
        print(f"\n🔍 DEBUGGING SLUG: {slug}")
        print(f"📊 Decodes to: {self.decode_slug(slug)}")
        
        try:
            start_time = time.time()
            
            # Navigate to the URL
            url = f"{self.base_url}{slug}"
            print(f"🌐 Testing URL: {url}")
            
            self.driver.get(url)
            
            # Wait longer for debugging
            time.sleep(3)
            
            # Get all the data
            page_source = self.driver.page_source
            page_title = self.driver.title
            final_url = self.driver.current_url
            content_length = len(page_source)
            load_time = time.time() - start_time
            
            print(f"📄 Page Title: '{page_title}'")
            print(f"🔗 Final URL: {final_url}")
            print(f"📏 Content Length: {content_length:,} characters")
            print(f"⏱️  Load Time: {load_time:.2f}s")
            
            # Check for error indicators
            page_source_lower = page_source.lower()
            error_indicators_found = []
            for indicator in self.error_indicators:
                if indicator.lower() in page_source_lower:
                    error_indicators_found.append(indicator)
            
            # Check for business indicators
            business_indicators_found = []
            for indicator in self.business_indicators:
                if indicator.lower() in page_source_lower:
                    business_indicators_found.append(indicator)
            
            print(f"❌ Error Indicators Found: {error_indicators_found}")
            print(f"✅ Business Indicators Found: {business_indicators_found}")
            
            # Show current scanner logic
            has_business_title = page_title and len(page_title) > 3 and page_title.lower() not in ['loading', 'error']
            has_substantial_content = content_length > 20000
            
            print(f"🏷️  Has Business Title: {has_business_title}")
            print(f"📊 Has Substantial Content (>20k): {has_substantial_content}")
            
            # Current scanner decision logic
            if not page_title or page_title.strip() == "":
                current_status = "ERROR_PAGE (Empty Title)"
            elif business_indicators_found or has_business_title or has_substantial_content:
                if error_indicators_found and not business_indicators_found and not has_business_title:
                    current_status = "ERROR_PAGE (Error indicators without business signs)"
                else:
                    current_status = "ACTIVE"
            elif error_indicators_found:
                current_status = "ERROR_PAGE (Error indicators found)"
            else:
                current_status = "INACTIVE_UNKNOWN (No indicators)"
            
            print(f"🤖 Current Scanner Would Mark As: {current_status}")
            
            # Show first 1000 characters of page source for manual inspection
            print(f"\n📝 PAGE SOURCE PREVIEW (first 1000 chars):")
            print("=" * 80)
            print(page_source[:1000])
            print("=" * 80)
            
            # Look for common business elements that might not be in our indicators
            business_keywords = [
                'calendar', 'date', 'time', 'slot', 'availability',
                'location', 'address', 'phone', 'contact',
                'price', 'cost', 'fee', 'payment',
                'staff', 'doctor', 'practitioner', 'therapist',
                'form', 'input', 'button', 'submit'
            ]
            
            found_keywords = []
            for keyword in business_keywords:
                if keyword in page_source_lower:
                    found_keywords.append(keyword)
            
            print(f"🔍 Additional Business Keywords Found: {found_keywords}")
            
            # Save full page source for detailed analysis
            debug_filename = f"debug_slug_{slug}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            with open(debug_filename, 'w', encoding='utf-8') as f:
                f.write(page_source)
            print(f"💾 Full page source saved to: {debug_filename}")
            
            return {
                'slug': slug,
                'decoded_number': self.decode_slug(slug),
                'url': url,
                'final_url': final_url,
                'page_title': page_title,
                'content_length': content_length,
                'load_time': load_time,
                'error_indicators_found': error_indicators_found,
                'business_indicators_found': business_indicators_found,
                'additional_keywords': found_keywords,
                'current_scanner_status': current_status,
                'has_business_title': has_business_title,
                'has_substantial_content': has_substantial_content,
                'debug_file': debug_filename
            }
            
        except Exception as e:
            print(f"❌ Error debugging slug {slug}: {e}")
            return None
    
    def run_debug_session(self):
        """Run debugging session for all test slugs"""
        if not self.setup_driver():
            return
        
        print("🚀 Starting Debug Session for 3 Slugs")
        print("=" * 60)
        
        results = []
        
        try:
            for slug in self.test_slugs:
                result = self.debug_slug(slug)
                if result:
                    results.append(result)
                time.sleep(2)  # Pause between tests
            
            # Save comprehensive debug report
            debug_report = {
                'debug_session': datetime.now().isoformat(),
                'base_url': self.base_url,
                'tested_slugs': self.test_slugs,
                'results': results,
                'scanner_indicators': {
                    'error_indicators': self.error_indicators,
                    'business_indicators': self.business_indicators
                }
            }
            
            report_filename = f"debug_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_filename, 'w', encoding='utf-8') as f:
                json.dump(debug_report, f, indent=2, ensure_ascii=False)
            
            print(f"\n📋 Debug report saved to: {report_filename}")
            
        finally:
            if self.driver:
                self.driver.quit()
                print("🔒 Browser closed")

if __name__ == "__main__":
    debugger = SlugDebugger()
    debugger.run_debug_session() 