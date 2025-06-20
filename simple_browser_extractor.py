#!/usr/bin/env python3
"""
Simple Browser-Based Business Data Extractor
Uses Selenium to wait for dynamic content and extract what's actually displayed
"""

import csv
import time
import json
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class SimpleBrowserExtractor:
    def __init__(self):
        self.base_url = "https://vsdigital-bookingwidget-prod.azurewebsites.net/widget-business/"
        self.results = []
        
        # Load sample slugs
        self.load_sample_slugs(10)  # Start with 10 for testing
    
    def load_sample_slugs(self, count=10):
        """Load sample slugs for testing"""
        try:
            with open('vsdhone_brands_smart.csv', 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                self.slugs = [row['slug'] for row in list(reader)[:count]]
            print(f"📁 Loaded {len(self.slugs)} sample slugs for testing")
        except FileNotFoundError:
            print("❌ Discovery CSV file not found")
            self.slugs = []
    
    def setup_driver(self):
        """Setup Chrome driver with appropriate options"""
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        
        # Enable logging
        options.add_argument('--enable-logging')
        options.add_argument('--log-level=0')
        
        try:
            driver = webdriver.Chrome(options=options)
            return driver
        except Exception as e:
            print(f"❌ Failed to setup Chrome driver: {e}")
            return None
    
    def extract_business_data(self, slug):
        """Extract business data for a single slug"""
        print(f"🔍 Extracting data for: {slug}")
        
        driver = self.setup_driver()
        if not driver:
            return None
        
        try:
            url = f"{self.base_url}{slug}"
            
            # Load the page
            driver.get(url)
            
            # Wait for page to load and give React time to render
            print(f"⏳ Waiting for page to load...")
            time.sleep(8)  # Give plenty of time for React to load
            
            # Get the final URL after any redirects
            final_url = driver.current_url
            page_title = driver.title
            
            business_data = {
                'slug': slug,
                'original_url': url,
                'final_url': final_url,
                'page_title': page_title,
                'business_name': '',
                'address': '',
                'phone': '',
                'email': '',
                'website': '',
                'description': '',
                'raw_text': '',
                'found_elements': [],
                'extraction_method': 'Browser Automation',
                'extracted_at': datetime.now().isoformat()
            }
            
            # Check if we were redirected to a different domain (like Hotel Capricorn example)
            if 'vsdigital-bookingwidget-prod.azurewebsites.net' not in final_url:
                print(f"🔗 Redirected to external site: {final_url}")
                business_data['extraction_method'] = 'External Redirect'
                business_data['business_name'] = page_title
                business_data['website'] = final_url
                
                # Try to extract contact info from the redirected page
                try:
                    # Look for contact information
                    contact_selectors = [
                        'a[href^="tel:"]', 'a[href^="mailto:"]', '.contact', '.phone', '.email', 
                        '.address', '.location', 'address'
                    ]
                    
                    for selector in contact_selectors:
                        elements = driver.find_elements(By.CSS_SELECTOR, selector)
                        for element in elements:
                            text = element.get_attribute('textContent') or element.text
                            href = element.get_attribute('href')
                            
                            if href and href.startswith('tel:'):
                                business_data['phone'] = href.replace('tel:', '').strip()
                            elif href and href.startswith('mailto:'):
                                business_data['email'] = href.replace('mailto:', '').strip()
                            elif text and len(text.strip()) > 3:
                                if not business_data['address'] and any(word in text.lower() for word in ['street', 'avenue', 'road', 'city']):
                                    business_data['address'] = text.strip()[:200]
                except Exception as e:
                    print(f"⚠️  Error extracting from redirected page: {e}")
            
            else:
                # We're still on the VSDHOne platform - look for widget content
                print(f"📱 Analyzing VSDHOne widget content...")
                
                # Wait for potential dynamic content
                try:
                    # Look for any loading indicators and wait for them to disappear
                    loading_selectors = ['.loading', '.spinner', '[class*="loading"]', '[class*="spinner"]']
                    for selector in loading_selectors:
                        try:
                            WebDriverWait(driver, 5).until(
                                EC.invisibility_of_element_located((By.CSS_SELECTOR, selector))
                            )
                        except:
                            pass
                except:
                    pass
                
                # Additional wait for any AJAX content
                time.sleep(3)
                
                # Get all visible text content
                body = driver.find_element(By.TAG_NAME, 'body')
                all_text = body.get_attribute('textContent') or body.text
                business_data['raw_text'] = all_text[:1000] if all_text else ''
                
                # Look for business information in various ways
                self.extract_widget_content(driver, business_data)
                
                # Check for network requests that might contain data
                self.check_network_requests(driver, business_data)
            
            print(f"✅ Extraction complete for {slug}")
            return business_data
            
        except Exception as e:
            print(f"❌ Error extracting {slug}: {e}")
            return {
                'slug': slug,
                'error': str(e),
                'extraction_method': 'Failed',
                'extracted_at': datetime.now().isoformat()
            }
        finally:
            driver.quit()
    
    def extract_widget_content(self, driver, business_data):
        """Extract content from the widget interface"""
        # Common selectors that might contain business info
        content_selectors = [
            'h1', 'h2', 'h3', '.title', '.name', '.business-name',
            '.contact', '.address', '.phone', '.email',
            '[data-testid]', '[id*="business"]', '[class*="business"]',
            'input[placeholder]', 'label', '.form-control'
        ]
        
        found_elements = []
        
        for selector in content_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    if element.is_displayed():
                        text = (element.get_attribute('textContent') or 
                               element.text or 
                               element.get_attribute('placeholder') or 
                               element.get_attribute('value') or '').strip()
                        
                        if text and len(text) > 2 and text not in found_elements:
                            found_elements.append(text)
                            
                            # Try to categorize the text
                            text_lower = text.lower()
                            if any(word in text_lower for word in ['phone', 'tel', '+1', '(', ')']) and not business_data['phone']:
                                business_data['phone'] = text[:50]
                            elif '@' in text and not business_data['email']:
                                business_data['email'] = text[:100]
                            elif any(word in text_lower for word in ['street', 'avenue', 'road', 'city', 'zip']) and not business_data['address']:
                                business_data['address'] = text[:200]
                            elif not business_data['business_name'] and len(text) < 100:
                                business_data['business_name'] = text
            except Exception:
                continue
        
        business_data['found_elements'] = found_elements[:20]  # Limit to first 20 elements
    
    def check_network_requests(self, driver, business_data):
        """Check browser network logs for API calls"""
        try:
            logs = driver.get_log('performance')
            api_calls = []
            
            for log in logs:
                try:
                    message = json.loads(log['message'])
                    if message['message']['method'] == 'Network.responseReceived':
                        url = message['message']['params']['response']['url']
                        if any(term in url.lower() for term in ['api', 'business', 'data', 'config']):
                            api_calls.append(url)
                except:
                    continue
            
            if api_calls:
                business_data['api_calls_detected'] = api_calls[:5]  # Limit to first 5
                print(f"📡 Detected API calls: {len(api_calls)}")
                
        except Exception as e:
            print(f"⚠️  Could not check network requests: {e}")
    
    def run_extraction(self, max_slugs=None):
        """Run extraction on the loaded slugs"""
        slugs_to_process = self.slugs[:max_slugs] if max_slugs else self.slugs
        
        print(f"🚀 Starting browser-based extraction for {len(slugs_to_process)} slugs...")
        
        for i, slug in enumerate(slugs_to_process, 1):
            print(f"\n📍 Processing {i}/{len(slugs_to_process)}: {slug}")
            
            result = self.extract_business_data(slug)
            if result:
                self.results.append(result)
            
            # Small delay between requests
            time.sleep(2)
        
        # Save results
        self.save_results()
        self.print_summary()
    
    def save_results(self):
        """Save extraction results to CSV"""
        if not self.results:
            print("No results to save")
            return
        
        filename = f'browser_extraction_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        
        # Get all possible fieldnames from all results
        all_fields = set()
        for result in self.results:
            all_fields.update(result.keys())
        
        fieldnames = sorted(list(all_fields))
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for result in self.results:
                # Convert list fields to strings
                for key, value in result.items():
                    if isinstance(value, list):
                        result[key] = '; '.join(str(v) for v in value)
                writer.writerow(result)
        
        print(f"💾 Results saved to: {filename}")
    
    def print_summary(self):
        """Print extraction summary"""
        if not self.results:
            return
        
        total = len(self.results)
        with_business_names = sum(1 for r in self.results if r.get('business_name', '').strip())
        with_phones = sum(1 for r in self.results if r.get('phone', '').strip())
        with_emails = sum(1 for r in self.results if r.get('email', '').strip())
        with_addresses = sum(1 for r in self.results if r.get('address', '').strip())
        redirected = sum(1 for r in self.results if r.get('extraction_method') == 'External Redirect')
        
        print(f"\n📊 EXTRACTION SUMMARY")
        print(f"=" * 40)
        print(f"Total slugs processed: {total}")
        print(f"Business names found: {with_business_names} ({with_business_names/total*100:.1f}%)")
        print(f"Phone numbers found: {with_phones} ({with_phones/total*100:.1f}%)")
        print(f"Email addresses found: {with_emails} ({with_emails/total*100:.1f}%)")
        print(f"Addresses found: {with_addresses} ({with_addresses/total*100:.1f}%)")
        print(f"External redirects: {redirected} ({redirected/total*100:.1f}%)")
        
        # Show successful extractions
        successful = [r for r in self.results if any(r.get(field, '').strip() for field in ['business_name', 'phone', 'email', 'address'])]
        
        if successful:
            print(f"\n✅ SUCCESSFUL EXTRACTIONS ({len(successful)}):")
            for result in successful[:10]:  # Show first 10
                name = result.get('business_name', 'Unknown')[:30]
                phone = result.get('phone', 'No phone')[:20]
                method = result.get('extraction_method', 'Unknown')
                print(f"  • {result['slug']}: {name} | {phone} | {method}")

if __name__ == "__main__":
    extractor = SimpleBrowserExtractor()
    
    # Start with a small test
    extractor.run_extraction(max_slugs=5) 