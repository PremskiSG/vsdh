#!/usr/bin/env python3
"""
Quick Browser Test - Test browser-based detection with known slugs
"""

import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

class QuickBrowserTest:
    def __init__(self):
        self.base_url = "https://vsdigital-bookingwidget-prod.azurewebsites.net/widget-business/"
        
        # Test slugs - 2 known working, 3 expected to be 401
        self.test_slugs = {
            'tc33l': 'Known Working - Altura Health (TX)',
            'ad31y': 'Known Working - The DRIPBaR Direct',  
            'aaaaa': 'Expected 401 Error',
            'aaaab': 'Expected 401 Error',
            'aaaac': 'Expected 401 Error'
        }
        
        print("🧪 Quick Browser Test for VSDHOne Detection")
        print("=" * 60)
        print(f"Testing {len(self.test_slugs)} slugs with browser automation")
        print("")
    
    def setup_driver(self):
        """Setup Chrome driver"""
        options = Options()
        options.add_argument('--headless')  # Run in background
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-logging')
        options.add_argument('--log-level=3')
        
        return webdriver.Chrome(options=options)
    
    def test_slug_with_browser(self, slug, description):
        """Test a single slug with browser automation"""
        print(f"🔍 Testing: {slug} ({description})")
        
        driver = self.setup_driver()
        
        try:
            url = f"{self.base_url}{slug}"
            print(f"   🌐 Loading: {url}")
            
            start_time = time.time()
            driver.get(url)
            
            # Wait for page to fully load and JavaScript to execute
            time.sleep(8)  # Give React time to load and render
            
            load_time = time.time() - start_time
            final_url = driver.current_url
            page_title = driver.title
            
            # Get page content after JavaScript execution
            try:
                body_element = driver.find_element(By.TAG_NAME, 'body')
                page_text = body_element.text.strip()
            except:
                page_text = ""
            
            print(f"   ⏱️  Load time: {load_time:.2f}s")
            print(f"   📏 Content length: {len(page_text)} chars")
            print(f"   🎯 Final URL: {final_url}")
            print(f"   📰 Page title: '{page_title}'")
            
            # Analyze the content
            page_text_lower = page_text.lower()
            
            # Business content indicators
            business_indicators = [
                'appointment', 'booking', 'schedule', 'clinic', 'medical', 
                'health', 'therapy', 'treatment', 'service', 'price', 
                'location', 'contact', 'phone', 'doctor', 'wellness',
                'altura health', 'dripbar', 'weight loss', 'injection'
            ]
            
            # Error page indicators
            error_indicators = [
                '401', 'error', 'nothing left to do here', 'go to homepage',
                'not found', 'access denied'
            ]
            
            # Count indicators
            business_count = sum(1 for indicator in business_indicators if indicator in page_text_lower)
            error_count = sum(1 for indicator in error_indicators if indicator in page_text_lower)
            
            print(f"   🏢 Business indicators found: {business_count}")
            print(f"   🚫 Error indicators found: {error_count}")
            
            # Show found indicators
            if business_count > 0:
                found_business = [ind for ind in business_indicators if ind in page_text_lower]
                print(f"   ✅ Business terms: {', '.join(found_business[:5])}")
            
            if error_count > 0:
                found_errors = [ind for ind in error_indicators if ind in page_text_lower]
                print(f"   ❌ Error terms: {', '.join(found_errors)}")
            
            # Determine page type
            is_error_page = (
                '401' in page_text_lower or 
                'nothing left to do here' in page_text_lower or
                error_count > 0
            )
            
            is_business_page = (
                business_count >= 2 and 
                not is_error_page and
                len(page_text) > 100
            )
            
            # Classification
            if is_error_page:
                print(f"   🚫 CLASSIFICATION: 401 ERROR PAGE")
            elif is_business_page:
                print(f"   🌟 CLASSIFICATION: ACTIVE BUSINESS PAGE")
            elif len(page_text) < 50:
                print(f"   ⚠️  CLASSIFICATION: MINIMAL CONTENT")
            else:
                print(f"   ❓ CLASSIFICATION: UNCLEAR CONTENT")
            
            # Show content preview
            preview = page_text[:200].replace('\n', ' ').replace('\r', ' ').strip()
            print(f"   📄 Content preview: {preview}")
            
        except Exception as e:
            print(f"   ❌ Browser Error: {e}")
        finally:
            try:
                driver.quit()
            except:
                pass
        
        print("")
    
    def run_test(self):
        """Run the quick browser test"""
        print(f"🚀 Starting quick browser test at {datetime.now().strftime('%H:%M:%S')}")
        print("")
        
        for i, (slug, description) in enumerate(self.test_slugs.items(), 1):
            print(f"[{i}/{len(self.test_slugs)}] " + "="*70)
            self.test_slug_with_browser(slug, description)
            
            if i < len(self.test_slugs):
                print("⏳ Waiting 3 seconds before next test...")
                time.sleep(3)
        
        print("🎯 QUICK BROWSER TEST COMPLETE")
        print("=" * 60)
        print("📋 Expected Results:")
        print("   • tc33l & ad31y should show: ACTIVE BUSINESS PAGE")
        print("   • aaaaa, aaaab, aaaac should show: 401 ERROR PAGE")

def main():
    tester = QuickBrowserTest()
    tester.run_test()

if __name__ == "__main__":
    main() 